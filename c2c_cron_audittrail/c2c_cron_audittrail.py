# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com)
# All Right Reserved
# Author Nicolas Bessi
#
##############################################################################
from datetime import datetime
import time
import threading

from dateutil.relativedelta import relativedelta

import netsvc
import tools
import pooler
from osv import fields, osv


def str2tuple(s):
    return eval('tuple(%s)' % (s or ''))

_intervalTypes = {
    'work_days': lambda interval: relativedelta(days=interval),
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=interval * 7),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class c2c_cron_audittrail(osv.osv):
    """c2c Cron Audittrail"""
    _inherit = "ir.cron"
    _columns = {
            'state': fields.selection([('ok', 'Ok'),
                                       ('cancel', 'Ko')], 'Status', readonly=True),
            'action_name': fields.char('Action Name', size=64, readonly=True),
            'duration': fields.float('Duration', readonly=True, help="Duration of scheduled action in Minutes"),
            'funct_message': fields.text("Function Message", readonly=True),
    }

    _lock = threading.Lock()
    RUNNING_CRON = set()

    def synchronized(f, _lock=_lock):
        """Decorator for thread-safety."""
        def wrapper(*args, **kwargs):
            _lock.acquire()
            try:
                return f(*args, **kwargs)
            finally:
                _lock.release()
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        return wrapper

    def _callback(self, db_name, uid, job, nextcall, numbercall, context=None):
        job_repr = "self.pool.get('%(model)s').%(function)s(cr, uid, *%(args)s)" % job
        self._logger.notifyChannel('timers', netsvc.LOG_INFO,
                                   'Job call of %s launched' % job_repr)
        m = self.pool.get(job['model'])
        if m and hasattr(m, job['function']):
            f = getattr(m, job['function'])
            key = (job['id'], db_name)
            args = str2tuple(job['args'])
            sql_params = {'id': job['id'], 'number': numbercall}
            time_before = datetime.now()
            try:
                db, pool = pooler.get_db_and_pool(db_name)
                cr = db.cursor()
                function = f(cr, uid, *args)
                if function is None:
                    function = "None"
                sql_params['state'] = 'ok'
                sql_params['msg'] = function
            except Exception, e:
                sql_params['state'] = 'cancel'
                sql_params['msg'] = e
                self._logger.notifyChannel('timers', netsvc.LOG_ERROR,
                                           'Job call of %s failed' % job_repr)
                self._logger.notifyChannel('timers', netsvc.LOG_ERROR,
                                           tools.exception_to_unicode(e))
            finally:
                time_after = datetime.now()
                sql_params['duration'] = (time_after - time_before).seconds / 60
                if numbercall:
                    # Reschedule the job in the future
                    while nextcall < datetime.now():
                        nextcall += _intervalTypes[job['interval_type']](job['interval_number'])
                    sql_params['next'] = nextcall.strftime('%Y-%m-%d %H:%M:%S')
                    sql_extra = 'nextcall = %(next)s'
                    job_status = 'rescheduled'
                else:
                    # If numbercall reach 0, deactivate the job
                    sql_extra = 'active = False'
                    job_status = 'deactivated'

                # Grab the lock before update
                self._lock.acquire()
                try:
                    # we use cursor as parent ir_cron class write function call the netsvc cancel function
                    # we do not use ORM due to strange behavior when active = False
                    cr.execute(
                        "UPDATE ir_cron"
                        "   SET funct_message = %(msg)s, duration = %(duration)s,"
                        "       state = %(state)s, numbercall = %(number)s, " +
                        sql_extra + " WHERE id = %(id)s", sql_params)

                    # To be sure that parallel process will never overlap in one DB
                    self.RUNNING_CRON.discard(key)
                finally:
                    cr.commit()
                    cr.close()
                    self._lock.release()

                self._logger.notifyChannel('timers', netsvc.LOG_INFO,
                                           'Job call of %s finished and job %s.' %
                                           (job_repr, job_status))

                # check=True: run once, do not schedule multiple "_poolJobs"
                self._poolJobs(db_name, check=True)

    @synchronized
    def _clearJobs(self, db_name):
        """Grab the lock and stop the timers."""
        # This method is used in "create", "write" and "unlink"
        # because the inherited methods are not thread-safe.
        self.cancel(db_name)
        self.RUNNING_CRON.clear()
        self._logger.notifyChannel('timers', netsvc.LOG_INFO, 'All jobs cancelled')

    @synchronized
    def _poolJobs(self, db_name, check=False):
        """Grab the lock and schedule the jobs."""
        try:
            db, pool = pooler.get_db_and_pool(db_name)
        except Exception:
            return False

        if not pool._init:
            jobs_to_schedule = []
            cr = db.cursor()
            try:
                cr.execute('SELECT * FROM ir_cron'
                           ' WHERE numbercall <> 0 AND active'
                           ' ORDER BY priority')
                for job in cr.dictfetchall():
                    numbercall = int(job['numbercall'])
                    key = (job['id'], db_name)
                    if numbercall and key not in self.RUNNING_CRON:
                        nextcall = datetime.strptime(job['nextcall'], '%Y-%m-%d %H:%M:%S')
                        if nextcall > datetime.now() or job['doall']:
                            self.RUNNING_CRON.add(key)
                            jobs_to_schedule.append((job, numbercall, nextcall))
            finally:
                cr.close()

            # Used to stagger cron jobs
            at_the_earliest = int(time.time()) + 5

            for job, numbercall, nextcall in jobs_to_schedule:
                self._logger.notifyChannel('timers', netsvc.LOG_INFO,
                    'Scheduling job "%(name)s" at %(nextcall)s' % job)
                next_call = time.mktime(nextcall.timetuple())
                if next_call < at_the_earliest:
                    # Jobs are staggered to prevent server overload.
                    # The delay is 10 seconds between consecutive jobs.
                    next_call = at_the_earliest
                    at_the_earliest += 10
                if numbercall > 0:
                    numbercall -= 1
                self.setAlarm(self._callback, next_call, db_name,
                              db_name, job['user_id'], job, nextcall, numbercall)

        if not check:
            # we ensure that _poolJobs runs at least every day
            next_call = int(time.time()) + (3600 * 24)
            self.setAlarm(self._poolJobs, next_call, db_name, db_name)

    def create(self, cr, uid, vals, context=None):
        res = super(c2c_cron_audittrail, self).create(cr, uid, vals, context=context)
        self._clearJobs(cr.dbname)
        self._poolJobs(cr.dbname)
        return res

    def write(self, cr, user, ids, vals, context=None):
        res = super(c2c_cron_audittrail, self).write(cr, user, ids, vals, context=context)
        self._clearJobs(cr.dbname)
        self._poolJobs(cr.dbname)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(c2c_cron_audittrail, self).unlink(cr, uid, ids, context=context)
        self._clearJobs(cr.dbname)
        self._poolJobs(cr.dbname)
        return res

c2c_cron_audittrail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

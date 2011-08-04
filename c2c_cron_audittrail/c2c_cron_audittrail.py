# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright © 2010-2011 Camptocamp SA (http://www.camptocamp.com)
# All Rights Reserved
# Author:       Nicolas Bessi
# Contributor:  Florent Xicluna
#
##############################################################################
from datetime import datetime
import logging
import time
import threading
import traceback

from dateutil.relativedelta import relativedelta

import netsvc
import pooler
from osv import fields, osv
try:
    from tools.safe_eval import safe_eval as eval
except ImportError:
    # some old version of OpenERP 5
    pass

# Minimal and maximal delay between "pool Jobs" calls (in seconds)
MIN_INTERVAL = 60           # 1 minute
MAX_INTERVAL = 3600 * 24    # 1 day

_intervalTypes = {
    'work_days': lambda interval: relativedelta(days=interval),
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=interval * 7),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


def str2tuple(s):
    return eval('tuple(%s)' % (s or ''))


def exc2str(e):
    return '%s: %s' % (type(e).__name__, e)


class Cron(object):
    """Singleton that run the cron tasks."""
    # Inspired from: https://bugs.launchpad.net/openobject-server/+bug/640493
    __nexttime = {}
    __cron = None

    @classmethod
    def set_task(cls, task):
        """Set the cron task.

        The task is a function with a single argument: the db_name.
        """
        cls.__cron = task

    @classmethod
    def set_interval(cls, db_name, interval):
        """Set the interval in seconds for this database."""
        assert cls.__cron is not None, 'No Cron task defined'
        cls.__nexttime[db_name] = time.time() + interval

    @classmethod
    def cancel(cls, db_name):
        """Turn off the cron for this database.

        If None is passed, all crons are disabled.
        """
        if db_name is None:
            cls.__nexttime.clear()
        else:
            try:
                del cls.__nexttime[db_name]
            except KeyError:
                pass

    @classmethod
    def runner(cls):
        """Main loop intended to be run in a dedicated thread."""
        while True:
            for (db_name, timestamp) in cls.__nexttime.items():
                if timestamp < time.time():
                    try:
                        cls.__cron(db_name)
                    except Exception, e:
                        # Safeguard to prevent early cron termination
                        log = logging.getLogger('cron').error
                        log('Uncaught exception!\n' + exc2str(e))
            time.sleep(MIN_INTERVAL)

def start_cron():
    cron_runner = threading.Thread(target=Cron.runner, name='Cron.runner')
    # the cron runner is a typical daemon thread, that will never quit and
    # must be terminated when the main process exits - with no consequence
    # (the processing threads it spawns are not marked daemon)
    cron_runner.setDaemon(True)     # compatibility Python 2.5
    cron_runner.start()

start_cron()


class c2c_cron_audittrail(osv.osv):
    """c2c Cron Audittrail"""
    _inherit = "ir.cron"
    _columns = {
        'state': fields.selection([('ok', 'Ok'),
                                   ('cancel', 'Ko')], 'Status', readonly=True),
        'action_name': fields.char('Action name', size=64, readonly=True),
        'duration': fields.float('Duration', readonly=True,
                                 help='Duration of scheduled action in minutes'),
        'funct_message': fields.text('Function message', readonly=True),
    }

    # forbid simultaneous calls of the same job
    _lock = {}
    _threads = {}
    _logger = logging.getLogger('cron')

    # This class inherits three methods from netsvc.Agent, but we use a
    # different logic here.  Only 'cancel' is really used.
    # For consistency we overwrite the three methods.
    setAlarm = quit = NotImplemented
    cancel = Cron.cancel

    def __init__(self, pool, cr):
        # Set the cron task
        Cron.set_task(self._poolJobs)
        # Cancel the netsvc.Agent, if it is running.  We don't use it.
        netsvc.Agent.cancel(cr.dbname)
        # Used to prevent race conditions
        self._lock[cr.dbname] = threading.Lock()
        return super(c2c_cron_audittrail, self).__init__(pool, cr)

    def _callback(self, db_name, uid, job, nextcall, numbercall, context=None):
        job_repr = "self.pool.get('%(model)s').%(function)s(cr, uid, *%(args)s)" % job
        self._logger.debug('Job call of %s launched' % job_repr)
        m = self.pool.get(job['model'])
        f = getattr(m, job['function'], None)
        if not callable(f):
            # Either m is None, f is None or f is not callable
            self._logger.warn('Cannot call job %s: model or method '
                              'does not exist.' % job_repr)
            return

        args = str2tuple(job['args'])
        sql_params = {
            'id': job['id'],
            'number': numbercall,
            'state': '',
            'msg': '',
        }
        if numbercall:
            # Reschedule the job in the future
            sql_params['next'] = nextcall.strftime('%Y-%m-%d %H:%M:%S')
            sql_extra = 'nextcall = %(next)s'
        else:
            # If numbercall reach 0, deactivate the job
            sql_extra = 'active = False'

        time_before = time.time()
        try:
            db, pool = pooler.get_db_and_pool(db_name)
            cr = db.cursor()
            result = f(cr, uid, *args)
            sql_params['state'] = 'ok'
            sql_params['msg'] = str(result)
            self._logger.debug('Job call of %s finished.' % job_repr)
        except Exception, e:
            cr.rollback()
            exc_tb = traceback.format_exc()
            sql_params['state'] = 'cancel'
            sql_params['msg'] = exc2str(e)
            self._logger.error('Job call of %s failed\n%s' %
                               (job_repr, exc_tb))
        finally:
            time_after = time.time()
            sql_params['duration'] = (time_after - time_before) / 60.

            # We use cursor because parent ir_cron class 'write' method
            # calls the 'cancel' method.
            # We do not use ORM due to strange behavior when active = False
            try:
                cr.execute(
                    'UPDATE ir_cron'
                    '   SET funct_message = %(msg)s, duration = %(duration)s,'
                    '       state = %(state)s, numbercall = %(number)s, ' +
                    sql_extra + ' WHERE id = %(id)s;', sql_params)
            finally:
                cr.commit()
                cr.close()

    def _start_thread(self, db_name, job, nextcall):
        key = (db_name, job['id'])
        t = self._threads.get(key)
        if t and t.isAlive():
            # Previous job call is still running
            return t.nextcall

        self._logger.info('Starting thread for job "%(name)s", '
                          'scheduled at %(nextcall)s' % job)

        # Update the numbercall
        numbercall = int(job['numbercall'])
        if numbercall > 0:
            numbercall -= 1

        # Update the nextcall
        if numbercall:
            interval = _intervalTypes[job['interval_type']](job['interval_number'])
            nextcall += interval
            if not job['doall']:
                # Reschedule the job in the future
                while nextcall < datetime.now():
                    nextcall += interval
        else:
            nextcall = False

        # Prepare and start the thread
        args = (db_name, job['user_id'], job, nextcall, numbercall)
        t = threading.Thread(target=self._callback, name=job['name'], args=args)
        self._threads[key] = t
        # force non-daemon task threads
        # (the Cron thread must be daemon, and this property is inherited by default)
        t.setDaemon(False)  # compatibility Python 2.5
        # Memorize the nextcall on the thread object itself
        t.nextcall = nextcall
        t.start()

        # Return the next call datetime, or False if no more call to schedule
        return nextcall

    def _poolJobs(self, db_name, check=False):
        """Start a thread for each job."""
        # This method can be called both by the "_MainThread"
        # and the "Cron.runner" thread.
        # We use a Lock to prevent a race condition.
        self._lock[db_name].acquire()
        try:
            return self.__poolJobs(db_name, check)
        except Exception, e:
            self._logger.error(exc2str(e))
        finally:
            self._lock[db_name].release()

    def __poolJobs(self, db_name, check=False):
        try:
            db, pool = pooler.get_db_and_pool(db_name)
            cr = db.cursor()
        except Exception:
            # database dropped or closed
            Cron.cancel(db_name)
            raise

        # Save the dbname for logging
        ct = threading.currentThread()
        ct.dbname = db_name

        now = datetime.now()
        next_calls = set()

        try:
            # Forget terminated threads
            for (key, t) in self._threads.items():
                if t.isAlive():
                    # Compatibility Python 2.5, Thread.name is the new API.
                    self._logger.info('Thread for job "%s" is still running' %
                                      (t.getName(),))
                else:
                    del self._threads[key]

            # Poll active cron jobs
            cr.execute('SELECT * FROM ir_cron'
                       ' WHERE numbercall <> 0 AND active'
                       ' ORDER BY priority;')
            for job in cr.dictfetchall():
                nextcall = datetime.strptime(job['nextcall'], '%Y-%m-%d %H:%M:%S')

                if not pool._init and nextcall < now:
                    nextcall = self._start_thread(db_name, job, nextcall)

                if nextcall:
                    next_calls.add(nextcall)
        finally:
            cr.commit()
            cr.close()

        if not check:
            if next_calls:
                td = min(next_calls) - now
                interval = td.seconds + td.days * 24 * 3600
                # Enforce minimal and maximal boundaries
                interval = min(max(interval, MIN_INTERVAL), MAX_INTERVAL)
            else:
                interval = MAX_INTERVAL
            Cron.set_interval(db_name, interval)
            self._logger.info('Next run scheduled in %s seconds' % (interval,))

    def restart(self, db_name):
        self.cancel(db_name)
        self._poolJobs(db_name)

c2c_cron_audittrail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

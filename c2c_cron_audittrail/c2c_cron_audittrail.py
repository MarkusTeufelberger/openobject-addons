#-*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
# Author Nicolas Bessi
#
##############################################################################
from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
import netsvc
import tools
import pooler
from osv import fields,osv

def str2tuple(s):
    return eval('tuple(%s)' % (s or ''))
    
_intervalTypes = {
    'work_days': lambda interval: relativedelta(days=interval),
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

class c2c_cron_audittrail(osv.osv):
    """c2c Cron Audittrail"""
    RUNNING_CRON=[]    
    _inherit="ir.cron"
    _columns={
            'state': fields.selection([('ok', 'Ok'),
                                              ('cancel', 'Ko')], 'Status', readonly=True),
            'action_name': fields.char('Action Name', size=64, readonly=True),
            'duration': fields.float('Duration', readonly=True, help="Duration of scheduler action in Minutes"),
            'funct_message':fields.text("Function Message", readonly=True),                                 
    }
    

    
    def _callback(self, db_name, uid, job, nextcall, numbercall, context=None):
        if context is None:
            context = {}
        key = (job['model'], job['function'], db_name)
        #job['user_id'], job['model'], job['function'], job['args']
        self._logger.notifyChannel('timers', netsvc.LOG_INFO, "Job call of self.pool.get('%s').%s(cr, uid, *%r) launched" % (job['model'], job['function'], job['args']))
        args = str2tuple(job['args'])
        m = self.pool.get(job['model'])
        if m and hasattr(m, job['function']):
            f = getattr(m, job['function'])
            try:
                db, pool = pooler.get_db_and_pool(db_name)
                cr = db.cursor()
                time_before = datetime.now()
                function = f(cr, uid, *args)
                if function == None:
                    function = "None"
                time_after = datetime.now()
                duration = time_after-time_before
                duration = duration.seconds/60
                #we use cursor as parent ir_cron class write function call the netsvc cancel function
                cr.execute("update ir_cron set funct_message = %s, duration = %s, state='ok' where id = %s", (function, duration, job['id']))  
                #self.write(cr, uid, [job['id']], {'funct_message': function, 'duration':duration, 'state': 'ok'},context={'call_from_self':True}) 
                #Normally if clause is not needed
                ##To be sure that parallel process will never be overlapping in one DB
                if key in self.RUNNING_CRON:
                    self.RUNNING_CRON.remove(key)
            except Exception, e:
                if key in self.RUNNING_CRON:
                    self.RUNNING_CRON.remove(key)
                #we use cursor as parent ir_cron class write function call the netsvc cancel function
                cr.execute("update ir_cron set state = 'cancel', funct_message = %s  where id = %s", (e,job['id']))   
                #self.write(cr, uid, [job['id']], {'state': 'cancel', 'funct_message': e}, context={'call_from_self':True})
                self._logger.notifyChannel('timers', netsvc.LOG_ERROR, "Job call of self.pool.get('%s').%s(cr, uid, *%r) failed" % job['model'], job['function'], job['args'])
                self._logger.notifyChannel('timers', netsvc.LOG_ERROR, tools.exception_to_unicode(e))
            finally:
                if numbercall :
                    while nextcall < datetime.now():
                        nextcall += _intervalTypes[job['interval_type']](job['interval_number'])
                addsql=''
                if not numbercall:
                    addsql = ', active=False'
                # we do not use ORM due to strange behavior when active = False 

                cr.execute("update ir_cron set nextcall=%s, numbercall=%s"+addsql+" where id=%s", (nextcall.strftime('%Y-%m-%d %H:%M:%S'), numbercall, job['id']))
                self._logger.notifyChannel('timers', netsvc.LOG_INFO, "Job call of self.pool.get('%s').%s(cr, uid, *%r) finished and reschedule at %s"\
                    % (job['model'], job['function'], job['args'], nextcall))
                cr.commit()
                cr.close()                
                self._poolJobs(db_name)
                
                 

    def _poolJobs(self, db_name, check=False): 
        try:
            db, pool = pooler.get_db_and_pool(db_name)
        except:
            return False        
        cr = db.cursor()
        try:
            if not pool._init:
                now = datetime.now()
                cr.execute('select * from ir_cron where numbercall<>0 and active order by priority')
                for job in cr.dictfetchall():
                    nextcall = datetime.strptime(job['nextcall'], '%Y-%m-%d %H:%M:%S')
                    numbercall = job['numbercall']
                    key = (job['model'], job['function'], db_name)
                    if numbercall and not key in self.RUNNING_CRON:
                        if numbercall > 0:
                            numbercall -= 1
                        if nextcall > datetime.now() or job['doall']:
                            next_call = time.mktime(time.strptime(job['nextcall'], '%Y-%m-%d %H:%M:%S'))
                            if next_call - time.time() < 0:
                                #Job will be launch in 5 seconds in case of do all and missed job
                                next_call =  int(time.time()) + 5
                            #We do not pass job as result in order to avoid
                            print job['function'],' planned'     
                            self.setAlarm(self._callback, next_call, db_name, db_name, job['user_id'], job ,nextcall, numbercall)
                            self.RUNNING_CRON.append(key)

            cr.execute('select min(nextcall) as min_next_call from ir_cron where numbercall<>0 and active and nextcall>=now()')
            next_call = cr.dictfetchone()['min_next_call']  
            if next_call:                
                next_call = time.mktime(time.strptime(next_call, '%Y-%m-%d %H:%M:%S'))
            else:
                next_call = int(time.time()) + 3600   # if do not find active cron job from database, it will run again after 1 day
            if not check:
                self.setAlarm(self._poolJobs, next_call, db_name, db_name)
        
        finally:
            cr.commit()
            cr.close()
            
    def create(self, cr, uid, vals, context=None):
        self.RUNNING_CRON=[]
        res = super(c2c_cron_audittrail, self).create(cr, uid, vals, context=context) 
        return res
        
    def write(self, cr, user, ids, vals, context=None):
        self.RUNNING_CRON=[]   
        res = super(c2c_cron_audittrail, self).write(cr, user, ids, vals, context=context)
        return res
        
    def unlink(self, cr, uid, ids, context=None):
        self.RUNNING_CRON=[]     
        res = super(c2c_cron_audittrail, self).unlink(cr, uid, ids, context=context)
        return res
                    
c2c_cron_audittrail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
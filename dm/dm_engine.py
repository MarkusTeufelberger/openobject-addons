# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import time

from osv import fields
from osv import osv
import sys
import datetime
import netsvc
import traceback
import tools
import pooler

# Enable/Disable performance monitoring
enable_monitor = False

class dm_perf_monitor(osv.osv): # {{{
    _name = "dm.perf_monitor"
    _descitption = "DM Performance Monitor"

    _columns = {
        'name' : fields.char('Function Name', size=64, required=True),
        'model' : fields.char('Model Name', size=64, required=True),
        'duration' : fields.float('Duration'),
        'date' : fields.datetime('Date'),
    }

    _defaults = {
        'date' : lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
dm_perf_monitor() # }}}

def monitor(func): # {{{
    if enable_monitor:
        def callf(*args, **kwargs):
            time_start = time.time()                
            r = func(*args, **kwargs)
            time_stop = time.time()
            duration = time_stop - time_start
            vals = {
                'name' : func.__name__,
                'duration' : duration,
                'model' : args[0],
            }
            pooler.get_pool(args[1].dbname).get('dm.perf_monitor').create(args[1], args[2], vals)
            return r
        return callf
    else:
        return func # }}}
    
class report_dm_performance_monitor(osv.osv):
    _name = "report.dm.performance.monitor"
    _description = "Performance monitor"
    _auto = False
    _columns = {
        'name' : fields.char('Function Name', size=64, required=True),
        'duration' : fields.float('Duration'),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_dm_performance_monitor')
        cr.execute("""
            create or replace view report_dm_performance_monitor as (
                select
                    min(p.id) as id,
                    p.name as name,
                    avg(p.duration) as duration
                from
                    dm_perf_monitor p
                group by p.name
            )""")
    
report_dm_performance_monitor()

class dm_workitem(osv.osv): # {{{
    _name = "dm.workitem"
    _description = "workitem"
    _SOURCES = [('address_id','Partner Address')]
    SELECTION_LIST = [('pending', 'Pending'), ('error', 'Error'), 
                      ('cancel', 'Cancelled'), ('freeze', 'Frozen'),
                      ('done', 'Done')]

    def _get_id(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        for wi in self.browse(cr, uid, ids, context):
            res[wi.id] = str(wi.id) or ''
        return res
        
    def _customer_id(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        for wi in self.browse(cr, uid, ids, context):
            res[wi.id] = wi.address_id and wi.address_id.id or ''
        return res

    def _customer_email(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        for wi in self.browse(cr, uid, ids, context):
            res[wi.id] = wi.address_id and wi.address_id.email or ''
        return res
    
    def id_search(self, cr, uid, obj, name, args, context={}):
        if not len(args):
            return []
        wi_id= args[0][2]
        if not wi_id:
            return []
        return [('id','in',[wi_id])]

    _columns = {
        'name': fields.function(_get_id, method=True, type='char',
                                string='ID',fnct_search=id_search),
        'step_id': fields.many2one('dm.offer.step', 'Offer Step',
                                    ondelete="cascade", select="1"),
        'segment_id': fields.many2one('dm.campaign.proposition.segment', 
                                      'Segments', select="1", 
                                       ondelete = "cascade"),
        'address_id': fields.many2one('res.partner.address', 
                                      'Customer Address',
                                       select="1",
                                       ondelete="cascade"),
        'customer_id': fields.function(_customer_id, method=True, type='char',
                                        string='Customer Id'),
        'customer_email': fields.function(_customer_email, method=True,
                                        type='char', string='Customer Email'),
        'action_time': fields.datetime('Action Time', select="1"),
        'source': fields.selection(_SOURCES, 'Source', required=True),
        'error_msg': fields.text('System Message'),
        'is_preview': fields.boolean('Document Preview Workitem'),
        'tr_from_id': fields.many2one('dm.offer.step.transition', 
                                      'Source Transition',
                                       ondelete="cascade"),
        'mail_service_id': fields.many2one('dm.mail_service','Mail Service'),
        'is_realtime': fields.boolean('Realtime Processing', select="1"),
        'state': fields.selection(SELECTION_LIST, 'Status', select="1"),
    }
    _defaults = {
        'source': lambda *a: 'address_id',
        'state': lambda *a: 'pending',
        'is_preview': lambda *a: False,
        'is_realtime': lambda *a: True,
        'action_time': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    def create(self,cr, uid, vals, context={}):
        id = super(dm_workitem,self).create(cr, uid, vals, context)
        obj = self.browse(cr, uid, id)
        if obj.is_realtime:
            wi_res = self.run(cr, uid, obj, context=context)
        return id

#    @tools.cache()
    @monitor
    def _check_sysmsg(self, cr, uid, code, context=None):
        """ Check action message code and set workitem log """
        sysmsg_id  = self.pool.get('dm.sysmsg').search(cr, uid, 
                                                [('code', '=', code)], 
                                                context=context)
        if sysmsg_id:
            sysmsg = self.pool.get('dm.sysmsg').browse(cr, uid, sysmsg_id,
                                                        context=context)[0]
            return {'state': sysmsg.state, 'msg': sysmsg.message, 
                                           'result': sysmsg.result}
        else:
            return {'state': 'error', 
                    'msg': "An unknown error has occured : %s" % code,
                    'result': False}

    @monitor
    def run(self, cr, uid, wi, context={}):
        logger = netsvc.Logger()
        context['active_id'] = wi.id
        done = False
        ms_err = ''

        try:
            server_obj = self.pool.get('ir.actions.server')
            tr_res = True

            """ Check if action must be done or cancelled by checking the 
                            condition code of incoming transitions """
            for tr in wi.step_id.incoming_transition_ids:
                eval_context = {
                    'pool': self.pool,
                    'cr': cr,
                    'uid': uid,
                    'wi': wi,
                    'tr': tr,
                }
                val = {}

                """ Evaluate condition code (for non preview workitems only)"""
                if wi.is_preview:
                    val['action'] = True
                else:
                    exec tr.condition_id.in_act_cond.replace('\r','') in \
                                                 eval_context, val

                if not val.get('action', False):
                    """ If action returned by the trigger code is 
                                                            False stop here """
                    tr_res = False
                    act_step = tr.step_from_id.name or False
                    break

            if tr_res:
                "Execute server action"
                wi_res = server_obj.run(cr, uid, [wi.step_id.action_id.id], context)
                if not wi_res and wi.step_id.action_id.state == 'object_create': 
                    # create object returns false ,asuming object is created
                    # state is set to done 
                    self.write(cr, uid, [wi.id], {'state': 'done',
                                    'error_msg': 'Case is created'})
                else :
                    """ Check returned code and set wi status """
                    wi_status = self._check_sysmsg(cr, uid, wi_res['code'],
                                                    context.copy())

                    "Set workitem state and message"
                    wr = self.write(cr, uid, [wi.id], {'state': wi_status['state'],
                                                    'error_msg':wi_status['msg']})
                    done = wi_status['result']
                    "If workitem done then execute mail service action"
                    if done:
                        doc_context = {}
                        doc_obj = self.pool.get(wi_res['model'])
                        for doc in doc_obj.browse(cr, uid, wi_res['ids']):
                            doc_context['active_id'] = doc.id
                            ms_res = server_obj.run(cr, uid,
                                            [doc.mail_service_id.action_id.id],
                                            doc_context)
                            ms_status = self._check_sysmsg(cr, uid, ms_res['code'], context)
                            doc_obj.write(cr, uid, [doc.id],
                                {'state': ms_status['state'],
                                'error_msg': 'err_msg' in ms_res and ms_res['err_msg'] or ms_status['msg'], 
                                'delivery_time': time.strftime('%Y-%m-%d  %H:%M:%S')})
                            " If doc in error, change workitem status "
                            if not ms_status['result']:
                                # Attention : if 1 doc crashes => wi in error but other docs processed
                                # TODO : Add doc in error ref in wi error_msg
                                wr = self.write(cr, uid, [wi.id], {'state': ms_status['state'],
                                                    'error_msg':ms_status['msg']})
                                done = False
            else:
                "Dont Execute Action if workitem is not to be processed"
                self.write(cr, uid, [wi.id], {'state': 'cancel',
                                    'error_msg': 'Cancelled by : %s'% act_step})

        except Exception, exception:
            tb = sys.exc_info()
            tb_s = "".join(traceback.format_exception(*tb))
            self.write(cr, uid, [wi.id], {'state': 'error',
            'error_msg': 'Exception: %s\n%s' % (tools.exception_to_unicode(exception), 
                                                                        tb_s)})
            netsvc.Logger().notifyChannel('dm action', netsvc.LOG_ERROR, 
            'Exception: %s\n%s' % (tools.exception_to_unicode(exception), tb_s))


        """ Check if it has to create next auto workitems """
        if done and not wi.is_preview and wi.step_id.outgoing_transition_ids:
            try:
                for tr in wi.step_id.outgoing_transition_ids:
                    if tr.condition_id and tr.condition_id.gen_next_wi:

                        """ Compute action time """
                        wi_action_time = datetime.datetime.strptime(wi.action_time,
                                                        '%Y-%m-%d  %H:%M:%S')
                        kwargs = {(tr.delay_type+'s'): tr.delay}
                        next_action_time = wi_action_time + datetime.timedelta(**kwargs)

                        if tr.action_hour:
                            """ If a static action hour is set, use it """
                            hour_str = str(tr.action_hour).split('.')[0] + ':' +\
                             str(int(int(str(tr.action_hour).split('.')[1]) * 0.6))
                            act_hour = datetime.datetime.strptime(hour_str, 
                                                                  '%H: % M')
                            next_action_time = next_action_time.replace(hour=act_hour.hour)
                            next_action_time = next_action_time.replace(minute=act_hour.minute)

                        if tr.action_day:
                            """ If a static action day of the month is set, use it """
                            next_action_time = next_action_time.replace(day=int(tr.action_day))
                            if next_action_time.day > int(tr.action_day):
                                next_action_time = next_action_time.replace(month=next_action_time.month + 1)

                        if tr.action_date:
                            """ If a static date is set, use it """
                            next_action_time = tr.action_date

                        aw_id = self.copy(cr, uid, wi.id, 
                                            {'step_id': tr.step_to_id.id,
                                           'tr_from_id': tr.id, 'error_msg': '',
                                            'is_realtime': False, 
                'action_time': next_action_time.strftime('%Y-%m-%d  %H:%M:%S')})

            except Exception, exception:
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                self.write(cr, uid, [wi.id],
                {'error_msg':'Error while creating auto workitem:\nException: \
                %s\n%s' % (tools.exception_to_unicode(exception), tb_s)})
                netsvc.Logger().notifyChannel('dm action - auto wi creation',
                netsvc.LOG_ERROR, 
                'Exception: %s\n%s' % (tools.exception_to_unicode(exception),
                 tb_s))

    def __init__(self, *args):
        self.is_running = False
        return super(dm_workitem, self).__init__(*args)

    def check_all(self, cr, uid, context={}):
        MAX_SIZE = 1000
        """ Check if the action engine is already running """
        if not self.is_running:

            """ Workitems processing """
            try:
                self.is_running = True

                """ Get workitems to process and run action """
                ids = self.search(cr, uid, [('state', '=', 'pending'),
                    ('action_time','<=', time.strftime('%Y-%m-%d %H:%M:%S')),
                    ('is_realtime', '=', False)])
                for wi in self.browse(cr, uid, ids[:MAX_SIZE], context=context):
                    wi_res = self.run(cr, uid, wi, context=context)
                    cr.commit()

            finally:
                self.is_running = False
                
            return True
        return False

dm_workitem() # }}}

class dm_event(osv.osv_memory): # {{{
    _name = "dm.event"
    _rec_name = "segment_id"

    _columns = {
        'segment_id': fields.many2one('dm.campaign.proposition.segment',
                                       'Segment', required=True),
        'step_id': fields.many2one('dm.offer.step', 'Offer Step', 
                                        required=True),
        'source': fields.selection([('address_id','Addresses')], 
                                   'Source', required=True),
        'address_id': fields.many2one('res.partner.address', 'Address'),
        'trigger_type_id': fields.many2one('dm.offer.step.transition.trigger',
                                           'Trigger Condition', required=True),
        'mail_service_id': fields.many2one('dm.mail_service', 'Mail Service'),
        'action_time': fields.datetime('Action Time'),
        'is_realtime': fields.boolean('Realtime Processing'),
    }
    _defaults = {
        'source': lambda *a: 'address_id',
    }

    @monitor
    def create(self, cr, uid, vals, context={}):
        id = super(dm_event,self).create(cr, uid, vals, context)
        obj = self.browse(cr, uid, id)

        tr_ids = self.pool.get('dm.offer.step.transition').search(cr, uid,
                               [('step_from_id', '=', obj.step_id.id),
                                ('condition_id', '=', obj.trigger_type_id.id)])
        if not tr_ids:
            netsvc.Logger().notifyChannel('dm event case', netsvc.LOG_WARNING,
                "There is no transition %s at this step : %s"% (obj.trigger_type_id.name,
                    obj.step_id.code))
            raise osv.except_osv('Warning',
                "There is no outgoing transition %s at this step : %s"% (obj.trigger_type_id.name,
                    obj.step_id.code))
            return False

        for tr in self.pool.get('dm.offer.step.transition').browse(cr, uid,
                                                                   tr_ids):
            if obj.action_time:
                action_time = datetime.datetime.strptime(obj.action_time, 
                                                         '%Y-%m-%d  %H:%M:%S')
            else:
                if obj.is_realtime:
                    action_time = datetime.datetime.now()
                else:
                    wi_action_time = datetime.datetime.now()
                    kwargs = {(tr.delay_type+'s'): tr.delay}
                    action_time = wi_action_time + datetime.timedelta(**kwargs)

                    if tr.action_hour:
                        hour_str =  str(tr.action_hour).split('.')[0] + \
                    ':' + str(int(int(str(tr.action_hour).split('.')[1]) * 0.6))
                        act_hour = datetime.datetime.strptime(hour_str,'%H:%M')
                        action_time = action_time.replace(hour=act_hour.hour)
                        action_time = action_time.replace(minute=act_hour.minute)

                    if tr.action_day:
                        action_time = action_time.replace(day=int(tr.action_day))
                        if action_time.day > int(tr.action_day):
                            action_time = action_time.replace(month=action_time.month + 1)

                    if tr.action_date:
                        action_time = tr.action_date

            try:
                workitem_id = self.pool.get('dm.workitem').create(cr, uid,
                                    {'step_id': tr.step_to_id.id or False, 
                                    'segment_id':obj.segment_id.id or False,
                                    'address_id': obj.address_id.id,
                                    'mail_service_id': obj.mail_service_id.id,
                      'action_time': action_time.strftime('%Y-%m-%d  %H:%M:%S'),
                      'tr_from_id': tr.id,'source': obj.source, 
                      'is_realtime': obj.is_realtime})
            except Exception, exception:
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                netsvc.Logger().notifyChannel('dm event', netsvc.LOG_ERROR,
              "Event cannot create Workitem: %s\n%s" % (str(exception), tb_s))
        return id

dm_event() # }}}

SYSMSG_STATES = [ # {{{
    ('draft','Draft'),
    ('open','Open'),
    ('close','Close'),
    ('pending','Pending'),
    ('cancel','Cancelled'),
    ('done','Done'),
    ('error','Error'),
] # }}}

class dm_sysmsg(osv.osv): # {{{
    _name = "dm.sysmsg"

    def _default_model(self, cr, uid, context={}):
        return self.pool.get('ir.model').search(cr, uid, 
                                            [('model', '=', 'dm.workitem')])[0]

    def _default_field(self, cr, uid, context={}):
        return self.pool.get('ir.model.fields').search(cr, uid, 
                                [('model_id', '=', 'workitem'),
                                 ('name', '=', 'error_msg')])[0]

    _columns = {
       'name': fields.char('Description', translate=True, size=64, 
                                                                required=True),
       'code': fields.char('Code', size=64, required=True),
       'message': fields.text('Message', translate=True),
       'state': fields.selection(SYSMSG_STATES, 'State to set'),
       'level': fields.integer('Level'),
       'model': fields.many2one('ir.model', 'Model', required=True),
       'field': fields.many2one('ir.model.fields', 'Field', required=True),
       'send_email': fields.boolean('Send Email'),
       'email_user': fields.many2one('res.users', 'Email User'),
       'result': fields.boolean('Action Result'),
    }
    _defaults = {
       'state': lambda *a: 'error',
       'level': lambda *a: 1,
       'model': _default_model,
       'field': _default_field,
    }
dm_sysmsg() # }}}

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

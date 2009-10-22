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
import datetime
import mx.DateTime
import tools
import netsvc
from osv import fields,osv
import os

global feedback_link 
global feedback_msg
feedback_link= 'http://localhost:8080/'
feedback_msg = 'Please visit the following link to give the feedback of'

class ctg_type(osv.osv):
    _name = 'ctg.type'
    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'code': fields.char('Code', size=64, required=True, select=True),
    }  
ctg_type()

class users(osv.osv):    
    _inherit = "res.users"
    _columns = {        
        'lp_login': fields.char('Launchpad ID', size=64),
        'ctg_line':fields.one2many('ctg.line','rewarded_user_id','CTG Lines', readonly=True),
        'user_history':fields.one2many('user.history','user_id','User History', readonly=True)
    }
users()

class ctg_line(osv.osv):
    _name = 'ctg.line'
    _columns = {        
        'ctg_type_id':fields.many2one('ctg.type', 'CTG Type', required=True),
        'rewarded_user_id':fields.many2one('res.users', 'Rewarded User', required=True),
        'points': fields.float('Points', required=True),
        'date_ctg':fields.date('CTG Date', required=True),
    }
    _defaults = {
        'points': lambda *a: 0.0,
        'date_ctg': lambda *a: time.strftime('%Y-%m-%d'),
    }
    _order = 'points desc'  

    def get_LP_points(self, cr, uid, automatic=False, use_new_cursor=False, context=None):                     
        from lp_server import LP_Server        
        user_obj = self.pool.get('res.users')
        ctg_type_obj = self.pool.get('ctg.type')
        lpserver = LP_Server()
        lpserver.cachedir = os.path.join(tools.config['root_path'],lpserver.cachedir)
        lpserver.credential_file = os.path.join(tools.config['root_path'],lpserver.credential_file)         
        lp = lpserver.get_lp()       
        user_ids = user_obj.search(cr, uid, [('lp_login','!=',False)])
        users = user_obj.read(cr, uid, user_ids, ['name','lp_login'])
        for user in users:
            user_res = lpserver.get_lp_people_info(lp, user['lp_login']) 
            type_ids = ctg_type_obj.search(cr, uid, [('code','=', 'development')])            
            if len(type_ids):
                ctg_ids = self.search(cr, uid, [('rewarded_user_id','=',user['id']),('ctg_type_id','=',type_ids[0])])
                ctg_res = self.read(cr, uid, ctg_ids, ['points','date_ctg'])                       
                points = 0.0
                for ctg in ctg_res:
                    points += float(ctg['points'])
                points = user_res[user['lp_login']]['karma'] - points
                if points > 0.0:
                    self.create(cr, uid, {'rewarded_user_id':user['id'],'ctg_type_id':type_ids[0],'points':points})    
        return True

    def send_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        # send mail to user regarding them CTG points of month by cron job
        if not context:
            context = {}
        date = context.get('date',False) or datetime.date.today()
        report_ctg_line_obj = self.pool.get('report.ctg.line')
        report_ctg_line_ids = report_ctg_line_obj.search(cr, uid, [('name','=',date.strftime('%Y:%m'))])   
        if len(report_ctg_line_ids):
            mail_body = {}
            for report_ctg_line in report_ctg_line_obj.browse(cr, uid, report_ctg_line_ids):
                user_address = report_ctg_line.rewarded_user_id.address_id
                if user_address and user_address.email:
                    values = mail_body.get(report_ctg_line.rewarded_user_id.id,[])                                        
                    values.append([
                            user_address.name,
                            user_address.email,
                            report_ctg_line.ctg_type_id.name,
                            report_ctg_line.points
                          ])
                    mail_body[report_ctg_line.rewarded_user_id.id] = values
            user_history_obj = self.pool.get('user.history')            
            for usr_id,values in mail_body.items():
                usr = True
                total = 0.0 
                action = "ctg_line"
                cr.execute("select max(date) as max_date from user_history where user_id = %s and action = '%s'"%(usr_id,action))
                history_ctg_lines = cr.dictfetchone()
                if history_ctg_lines['max_date']:
                    last_date = history_ctg_lines['max_date']
                    cr.execute("""select sum(points) as old_points from ctg_line
                                  where date_ctg <= '%s' and rewarded_user_id =%s """%(last_date,str(usr_id)))
                    old_total = cr.fetchone()[0]
                else:
                    old_total = 0.0
                    last_date = date.strftime('%Y-%m-%d')
                for user, mail_to, ctg_type, points in values:
                    if not user:
                        user = ''
                    if usr:
                        body ="<html><body>Hello <b>" + user + "</b>!<br>" 
                        body = body +"<p style=\"margin-left:35px\"> Thanks to Contribute on OpenERP/OpenObject during <b>"+ last_date + "</b> and <b>" + date.strftime('%Y-%m-%d') +"</b><br>"\
                                       + "Your CTG points are decribe in following table."\
                                       + "Your CTG Ponits table:</p>"\
                                       + "<p style=\"margin-left:70px\"><table><tr><th align=left>CTG Type</th><th align=center>|</th><th align=right>Points</th></tr>"\
                                       + "<tr><td colspan=3><hr></td></tr>" 
                        usr = False 
                    body = body + "<tr><td align=left>" + ctg_type + "</td><td align=center>|</td><td align=right>" + str(points) + "</td></tr>"
                    total = total + points       
                cr.execute("select sum(points) as total1 from ctg_line where rewarded_user_id=%s " %str(usr_id))
                total1 = cr.fetchone()[0]
                if total1 == old_total:
                    body = ''
                    body ="<html><body>Hello <b>" + user + "</b>!<br>"\
                           +"<p style=\"margin-left:35px\"> Thanks to Contribute on OpenERP/OpenObject during <b>"+ last_date + "</b> and <b>" + date.strftime('%Y-%m-%d') +"</b><br>"\
                           + "Your CTG points are decribe in following table."\
                           + "Your CTG Ponits table:</p>"\
                           + "<p style=\"margin-left:70px\"><table><tr><th align=left>CTG Type</th><th align=center>|</th><th align=right>Points</th></tr>"\
                           + "<tr><td colspan=3><hr></td></tr>"\
                           + "<tr><td align=left>" + ctg_type + "</td><td align=center>|</td><td align=right>" + str(0.00) + "</td></tr>"\
                           + "<tr><td></td><td align=center>|</td><td></td></tr>"\
                           + "<tr><td colspan=3><hr></td></tr>"\
                           + "<tr><td align=left>Total</td><td align=center>|</td><td align=right>" + str(0.00) + "</td></tr></table></p>"\
                           + "<p style=\"margin-left:35px\">And Total CTG points upto <b>" + date.strftime('%Y-%m-%d') +"</b> : <b>" + str(0.00) + "</b></p>"\
                           + "Thanks<br>OpenERP Quality Team</body></html>"
                else:
                    body = body + "<tr><td></td><td align=center>|</td><td></td></tr>"\
                            + "<tr><td colspan=3><hr></td></tr>"\
                            + "<tr><td align=left>Total</td><td align=center>|</td><td align=right>" + str(total) + "</td></tr></table></p>"\
                            + "<p style=\"margin-left:35px\">And Total CTG points upto <b>" + date.strftime('%Y-%m-%d') +"</b> : <b>" + str(total1) + "</b></p>"\
                            + "Thanks<br>OpenERP Quality Team</body></html>"
                user = tools.config['email_from']
                if not user:
                    raise osv.except_osv(_('Error'), _("Please specify server option --smtp-from !"))
                
                subject = 'Your CTG points of %s month in OpenERP' %(date.strftime('%Y:%m'))
                logger = netsvc.Logger()
                if tools.email_send(user, [mail_to], subject, body, debug=False, subtype='html') == True:
                    logger.notifyChannel('email', netsvc.LOG_INFO, 'Email successfully send to : %s' % (mail_to))
                    user_history_obj.create(cr,uid,{'action':action,'description':subject,'date':date,'user_id':usr_id})
                else:
                    logger.notifyChannel('email', netsvc.LOG_ERROR, 'Failed to send email to : %s' % (mail_to))
        return True
    
    
ctg_line()

class report_ctg_line(osv.osv):
    _name = "report.ctg.line"
    _description = "CTG points per user per month"
    _auto = False
    _columns = {
        'name' : fields.char('Month',size=64),
        'ctg_type_id': fields.many2one('ctg.type', 'CTG Type'),
        'points': fields.float('Points', required=True),
        'rewarded_user_id':fields.many2one('res.users', 'Rewarded User', required=True),
    }
    _order = 'name desc'

    def init(self, cr):
        cr.execute("""
            create or replace view report_ctg_line as ( 
                select 
                    min(l.id) as id,
                    to_char(l.date_ctg,'YYYY:mm') as name,
                    sum(l.points) as points,                    
                    l.rewarded_user_id,
                    l.ctg_type_id
                from ctg_line l                
                group by
                    to_char(l.date_ctg,'YYYY:mm'), l.rewarded_user_id, l.ctg_type_id
            )""")
report_ctg_line()

class ctg_feedback(osv.osv):
    _name = 'ctg.feedback'
    _columns = {
        'name': fields.char('Title', size=64, required=True, select=True),
        'ctg_line_id':fields.many2one('ctg.line', 'CTG', readonly=True),
        'ctg_type_id':fields.many2one('ctg.type', 'CTG Type', required=True),
        'user_to':fields.many2one('res.users', 'Feedback by User', required=True),
        'responsible':fields.many2one('res.users', 'Responsible User', required=True),
        'points': fields.selection([
            ('0','Not Satisfacted At All'),
            ('3','Not Satisfacted'),
            ('6','Satisfacted'),
            ('10','Very Satisfacted'),            
            ], 'Points'),
        'date_feedback':fields.date('Feedback Date', required=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('open','Open'),
            ('done','Done'),
            ('cancel','Canceled'),            
            ], 'State', required=True),
        'note': fields.text('Body'),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'date_feedback': lambda *a: time.strftime('%Y-%m-%d'),
    }
    _order = 'name desc'  

    def action_cancel(self, cr, uid, ids, context={}):
        return self.write(cr, uid, ids, {'state':'cancel'})
        
    def action_open(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'open'})
        # TODO create a link to feedback to send it in the body of the mail to the user
        feedback_lines = self.browse(cr,uid,ids)
        # send mail to the user for feedback 
        for feedback_line in feedback_lines:
            subject = feedback_line['name']  
            user = tools.config['email_from']
            if not user:
                raise osv.except_osv(_('Error'), _("Please specify server option --smtp-from !"))
            if feedback_line.user_to.address_id and feedback_line.user_to.address_id.email:
                open_feedback_user_action_id = self.pool.get('ir.model.data').search(cr ,uid, [('name','=','action_view_open_related_user_ctg_feedback')])
                open_feedback_user_action_obj = self.pool.get('ir.model.data').browse(cr, uid, open_feedback_user_action_id, context)[0]
                self.pool.get('res.users').write(cr ,uid, [feedback_line.user_to.id], {'action_id':open_feedback_user_action_obj.res_id})
                mail_to = feedback_line.user_to.address_id.email
                body = 'Hello %s,\n %s %s.\n %s'%(feedback_line.user_to.name, feedback_msg, feedback_line['name'],feedback_link)
                logger = netsvc.Logger()
                if tools.email_send(user, [mail_to], subject, body, debug=False, subtype='html') == True:
                    logger.notifyChannel('email', netsvc.LOG_INFO, 'Email successfully send to : %s' % (mail_to))
                    date = feedback_line.date_feedback or datetime.date.today()
                    usr_id = feedback_line.user_to.id
                    feedback_id = feedback_line.id  
                    #self.pool.get('user.history').create(cr,uid,{'action':'feedback', 'description':subject, 'feedback_id':feedback_line.id,'date':date, 'user_id':usr_id})
                else:
                    logger.notifyChannel('email', netsvc.LOG_ERROR, 'Failed to send email to : %s' % (mail_to))
        return True            

    def action_done(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'done'})
        # TODO : create CTG Line with ctg_type ?
        feedback_lines = self.browse(cr,uid,ids)
        ctg_line_obj = self.pool.get('ctg.line')
        for feedback_line in feedback_lines:
            #if feedback_line.ctg_type_id.code == 'sales' or feedback_line.ctg_type_id.code == 'dms':
            related_project_ids = self.pool.get('project.project').search(cr, uid, [('manager','=',int(feedback_line.responsible.id))])
            count = len(related_project_ids)
            avg_point = int(feedback_line.points)/count
            if feedback_line.points:
               ctg_line_obj.create(cr, uid,{
                        'ctg_type_id':feedback_line.ctg_type_id.id,
                        'rewarded_user_id':feedback_line.responsible.id,
                        'points':avg_point,
                        'date_ctg': feedback_line.date_feedback})
            else:
                raise osv.except_osv(_('Usererror !'),
                        _('Please Select Points For Feedback.'))
        return True                    
    def action_cancel_draft(self, cr, uid, ids, context={}):
        return self.write(cr, uid, ids, {'state':'draft'})

    def check_feedback(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        # draft to open feedback . It is called by cron job
        draft_feedback_ids = self.search(cr, uid, [('date_feedback','<=',time.strftime('%Y-%m-%d')),('state','=','draft')])
        if len(draft_feedback_ids):
            self.action_open(cr, uid, draft_feedback_ids, context=context)

        # open to cancel feedback if it is not done since long time (1 month)
        current_date = datetime.date.today()
        year = current_date.year
        if current_date.month == 1:
            year = current_date.year - 1
            month = 12
            days = current_date.day
        else:
            # if previous month has less days the current month and current_date is last date
            month = current_date.month - 1
            ref_date = current_date
            rel_date = ref_date.replace(month=month+1, day=1) - datetime.timedelta(days=1)
            if current_date.day > rel_date.day:
                days = rel_date.day
            else:
                days = current_date.day
        d = datetime.date(year, month, days)
        open_feedback_ids = self.search(cr, uid, [('date_feedback','<=',d.strftime('%Y-%m-%d')),('state','=','open')])  
        if len(open_feedback_ids):
            self.action_cancel(cr, uid, open_feedback_ids, context=context)
        return True
ctg_feedback()

class user_history(osv.osv):
    _name = "user.history"
    _rec_name ="user_id"
    _description = "User History"
    _columns = {
                'action':fields.selection([('feedback', 'Feedback'), ('ctg_line', 'CTG Line')],'Action'),
                'feedback_id':fields.many2one('ctg.feedback', 'Feedback'),
                'description':fields.char('Description', size=64),
                'date':fields.date('Sent Date'),
                'user_id':fields.many2one('res.users', 'Responsible', required=True),
                
              }
user_history()


class document_file(osv.osv):
    _inherit = 'ir.attachment' 
    
    def read(self, cr, user, ids, fields_to_read=None, context=None, load='_classic_read'):
        result = super(document_file,self).read(cr, user, ids, fields_to_read, context=context, load=load)
        feedback_date = datetime.date.today() + datetime.timedelta(days=2)
        ctg_type_obj = self.pool.get('ctg.type')
        ctg_type_ids = ctg_type_obj.search(cr,user,[('code','=','dms')])
        if len(ctg_type_ids) and context.get('download',False):
            ctg_feedback_obj = self.pool.get('ctg.feedback')
            for res in result:
                cr.execute('select name,title,user_id from ir_attachment where id = %s' %(res['id']))
                document = cr.dictfetchone()
                ctg_feedback_id = ctg_feedback_obj.create(cr, user, {
                        'name' : '%s Document' %(document['title']),                        
                        'ctg_type_id': ctg_type_ids[0],
                        'user_to':user,
                        'responsible':document['user_id'],        
                        'date_feedback': feedback_date.strftime('%y-%m-%d')}, context)
        return result

document_file()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    #Hint : What to Do ? If Remove the Invoice.
    
    def action_move_create(self, cr, uid, ids, *args): 
        result = super(account_invoice,self).action_move_create(cr, uid, ids, args)
        ctg_line_obj = self.pool.get('ctg.line')
        ctg_type_obj = self.pool.get('ctg.type')
        ctg_type_ids = ctg_type_obj.search(cr,uid,[('code','=','sales')])
        new_date = datetime.date.today()
        for invoice in self.browse(cr,uid,ids):
            if len(ctg_type_ids):
                if invoice.user_id:
                    ctg_line_obj.create(cr, uid,{
                            'ctg_type_id':ctg_type_ids[0],
                            'rewarded_user_id':invoice.user_id.id,
                            'date_ctg': new_date,
                            'points':invoice.amount_untaxed})
        return result
    
    def action_cancel(self, cr, uid, ids, *args):
        ctg_type_obj = self.pool.get('ctg.type')
        ctg_line_obj = self.pool.get('ctg.line')
        invoices = self.browse(cr,uid,ids)            
        ctg_type_ids = ctg_type_obj.search(cr,uid,[('code','=','sales')])
        for invoice in invoices:
            if invoice.state == 'open':
                if len(ctg_type_ids):
                    if invoice.user_id:
                        ctg_line_obj.create(cr, uid, {
                                    'ctg_type_id': ctg_type_ids[0],
                                    'rewarded_user_id' : invoice.user_id.id,
                                    'points':-invoice.amount_untaxed
                                    })      
        result = super(account_invoice,self).action_cancel(cr, uid, ids, args)             
        return result 
    
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def create(self, cr, uid, vals, context={}):
        result = super(account_invoice_line,self).create(cr, uid, vals, context) 
        if vals.has_key('account_analytic_id') and vals['account_analytic_id']:            
            project_obj = self.pool.get('project.project')      
            feedback_obj = self.pool.get('ctg.feedback')
            user_obj = self.pool.get('res.users')
            project_ids = project_obj.search(cr, uid, [('category_id','=',vals['account_analytic_id'])])
            projects = project_obj.browse(cr, uid, project_ids)
            ctg_type_ids = self.pool.get('ctg.type').search(cr,uid,[('code','=','customer satisfaction')])
            feedback_date = datetime.date.today() + datetime.timedelta(days=2)
            invoice_rec = self.pool.get('account.invoice').browse(cr,uid,vals['invoice_id'])
            dedicated_user = False
            for address in invoice_rec.partner_id.address:
                user_ids = user_obj.search(cr, uid, [('address_id','=',address.id)])
                if len(user_ids):
                    dedicated_user = user_ids[0]
                    break
            if len(ctg_type_ids) and dedicated_user:
                for project in projects:
                        feedback_obj.create(cr, uid, {
                                    'name':'%s Project' %(project.name),
                                    'ctg_type_id':ctg_type_ids[0],
                                    'user_to':dedicated_user,
                                    'responsible':project.manager.id,
                                    'date_feedback':feedback_date,
                        })
        return result

account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

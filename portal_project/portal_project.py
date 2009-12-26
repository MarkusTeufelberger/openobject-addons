# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime

from osv import fields, osv
import pooler
import tools
from tools.config import config
from tools.translate import _
import netsvc

AVAILABLE_STATES = [
    ('draft','Draft'),
    ('open','Open'),
    ('cancel', 'Cancelled'),
    ('done', 'Closed'),
    ('pending','Pending')
]

def _project_get(self, cr, uid, context={}):
    obj = self.pool.get('project.project')
    ids = obj.search(cr, uid, [])
    res = obj.read(cr, uid, ids, ['id','name'], context)
    res = [(str(r['id']),r['name']) for r in res]
    return res

class users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'user_id': fields.many2one('project.project', 'portal', ondelete='cascade'),
        'context_project_id': fields.selection(_project_get, 'Project'),
        }

    def context_get(self, cr, uid, context=None):
        return super(users, self).context_get(cr, uid, context)

users()

class project_project(osv.osv):
    _inherit = "project.project"
    _description = "Project"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('action_portal') and context['action_portal']=='project' and context.has_key('project_id') and context['project_id']:
            return [context['project_id']]
        return super(project_project, self).search(cr, uid, args, offset, limit, order, context, count)


    def _get_details(self, cr, uid, ids_project, context={}, *arg):
        # Todo: 1. Reload button gives error for project
        #       2. Test/Check
        if not ids_project:
            return {}
        result = {}
        for id in ids_project:
            result[id] = {
                  'tasks_detail': '',
                  'bugs': '',
                  'features': '',
                  'support_req': '',
                  'doc': ''
                          }
        ids = ",".join(map(str, ids_project))

        # Number of tasks
        cr.execute('select count(t.id), p.id, p.name , sum(t.remaining_hours) as hours \
                    from project_project as p left join project_task as t on p.id=t.project_id \
                    where p.id in ('+ids+') and t.state=%s group by p.id, p.name', ('open',))
        for proj in cr.dictfetchall():
            result[proj['id']]['tasks_detail'] = str(proj['count']) + ' opens, ' + str(proj['hours']) + ' hours remaining'

        #======================================Bug, Features ,support request====================================================
        cr.execute('select p.id, count(c.id),c.state,p.name from project_project as  p, \
                    crm_case as c where p.id=c.project_id and p.section_bug_id=c.section_id \
                    and p.id in ('+ids+') and c.state=%s group by p.id,p.name,c.state', ('open',))
        res_bug = cr.dictfetchall()
        for bug in res_bug:
            result[bug['id']]['bugs'] = result[bug['id']]['bugs'] + str(bug['count']) + ' Open '
        cr.execute('select p.id, count(c.id), p.name from project_project as p, \
                    crm_case as c where p.id=c.project_id and p.section_bug_id=c.section_id \
                    and p.id in ('+ids+') group by p.id,p.name')
        for bug in cr.dictfetchall():
            result[bug['id']]['bugs'] = result[bug['id']]['bugs'] +  str(bug['count'])  +  ' Total'

        cr.execute('select p.id, count(c.id),c.state,p.name from project_project as  p, \
                    crm_case as c where p.id=c.project_id and p.section_feature_id=c.section_id \
                    and p.id in ('+ids+') and c.state=%s group by p.id,p.name,c.state', ('open',))
        res_fet = cr.dictfetchall()
        for feature in res_fet:
            result[feature['id']]['features'] = result[feature['id']]['features'] + str(feature['count']) + ' Open '
        cr.execute('select p.id, count(c.id), p.name from project_project as p, \
                    crm_case as c where p.id=c.project_id and p.section_feature_id=c.section_id \
                    and p.id in ('+ids+') group by p.id,p.name')
        for feature in cr.dictfetchall():
            result[feature['id']]['features'] = result[feature['id']]['features'] + str(feature['count']) + ' Total'

        cr.execute('select p.id, count(c.id),c.state,p.name from project_project as  p, \
                    crm_case as c where p.id=c.project_id and p.section_support_id=c.section_id \
                    and p.id in ('+ids+') and c.state=%s group by p.id,p.name,c.state', ('open',))
        res_sup = cr.dictfetchall()
        for support in res_sup:
            result[support['id']]['support_req'] = result[support['id']]['support_req'] + str(support['count']) + ' Open '
        cr.execute('select p.id, count(c.id), p.name from project_project as p, \
                    crm_case as c where p.id=c.project_id and p.section_support_id=c.section_id \
                    and p.id in ('+ids+') group by p.id,p.name ')
        for support in cr.dictfetchall():
            result[support['id']]['support_req'] = result[support['id']]['support_req'] + str(support['count']) + ' Total'

        #==========================================================================================

        # Number of doument attach in project and its tasks
        model = 'project.project'
        cr.execute('select count(i.id), p.id, p.name from project_project as p \
                    left join ir_attachment as i on i.res_id=p.id where p.id in ('+ids+') \
                    and i.res_model=%s group by p.id, p.name',(model,))
        for doc in cr.dictfetchall():
            result[doc['id']]['doc'] = doc['count']#str(doc['count'])
        cr.execute('select count(i.id), p.id, p.name, i.file_size as datas from project_project as p \
                    left join ir_attachment as i on i.res_id=p.id where p.id in ('+ids+') and \
                    i.res_model=%s group by p.id, p.name, i.file_size',(model,))
        res_size_proj = cr.dictfetchall()
        cr.execute('select count(i.id) as task_docs, p.id as project from project_task t \
                    left join project_project p on p.id=t.project_id left join ir_attachment i on \
                    i.res_id=t.id where p.id in ('+ids+') and i.res_model=%s group by p.id',('project.task',))
        task_res = cr.dictfetchall()
        for doc in task_res:
            if result[doc['project']]['doc'] == '': result[doc['project']]['doc'] = 0
            result[doc['project']]['doc'] = str(result[doc['project']]['doc'] +  doc['task_docs'])#str(doc['count'])

        cr.execute('select t.id as task_id, count(i.id) as task_docs, p.id as project, i.file_size \
                    from project_task t left join project_project p on p.id=t.project_id \
                    left join ir_attachment i on i.res_id=t.id where p.id in ('+ids+') and i.res_model=%s \
                    group by p.id, i.file_size, t.id', ('project.task',))
        res_size_task = cr.dictfetchall()

        dict_size = {}
        for id in ids_project:
            dict_size.setdefault(id, 0)
        for doc in res_size_proj:
            dict_size[doc['id']] += doc['datas'] # To be test
        for doc in res_size_task:
            dict_size[doc['project']] += doc['file_size'] # To be test
        for s in dict_size:
            size = ''
            if dict_size[s] >= 1073741824:
                size = str((dict_size[s]) / 1024 / 1024 / 1024) + ' GB'
            elif dict_size[s] >= 1048576:
                size = str((dict_size[s]) / 1024 / 1024) + ' MB'
            elif dict_size[s] >= 1024:
                size = str((dict_size[s]) / 1024) + ' KB'
            elif dict_size[s] < 1024:
                size = str(dict_size[s]) + ' bytes'
            if result[s]['doc'] == '':
                result[s]['doc'] = '0'
            result[s]['doc'] = str(result[s]['doc']) + ' for ' +  size
        return result

    def _get_users(self, cr, uid, ids, context={}, *arg):
        if not ids:
            return {}
        res = {}
        list_user=[]
        for data_project in self.browse(cr, uid, ids, context):
                for user in data_project.members:
                    list_user.append(user.id)
                res[data_project.id] = list_user
        return res

    def _get_announces(self, cr, uid, ids, context={}, *arg):
        if not ids:
            return {}
        res = {}
        date_back = datetime.date.today() +  datetime.timedelta(days=-31)
        date_back = date_back.strftime('%Y-%m-%d')
        for announce in self.browse(cr, uid, ids, context):
            cr.execute("""select c.id from crm_case c left join project_project p on %s = c.project_id \
                       where c.section_id = p.section_annouce_id and c.date >= %s """, (announce.id, date_back))
            list_announce = map(lambda x: x[0], cr.fetchall())
            res[announce.id] = list_announce
        return res

    def _get_hours(self, cr, uid, ids, context={}, *arg):
        res = {}
        if not ids:
            return {}
        for id in ids:
            for acc in self.browse(cr, uid, ids, context):
                cr.execute("""select id from account_analytic_line where account_id in \
                            (select category_id from project_project where id = %s)""" %id)
                line_id = map(lambda x: x[0], cr.fetchall())
                res[acc.id] = line_id
        return res

    _columns = {
        'section_bug_id': fields.many2one('crm.case.section', 'Bug Section'),
        'section_feature_id': fields.many2one('crm.case.section', 'Feature Section'),
        'section_support_id': fields.many2one('crm.case.section', 'Support Section'),
        'section_annouce_id': fields.many2one('crm.case.section', 'Announce Section'),
        'tasks_detail': fields.function(_get_details, type='char', size=64, method=True, string='Tasks', multi='project', help='Show open tasks for Project with remaining hours'),
        'bugs': fields.function(_get_details, type='char', size=64, method=True, string='Bugs', multi='project'),
        'features': fields.function(_get_details, type='char', size=64, method=True, string='Features',multi='project'),
        'support_req': fields.function(_get_details, type='char', size=64, method=True,multi='project', string='Support Requests'),
        'doc': fields.function(_get_details, type='char', method=True, size=64, multi='project', string='Documents'),
        'announce_ids': fields.function(_get_announces , type='one2many' , relation='crm.case', method=True , string='Announces'),
        'member_ids': fields.function(_get_users, type='one2many', relation='res.users' , method=True , string='Project Members'),
        'bugs_ids':fields.one2many('report.crm.case.bugs', 'project_id', 'Bugs'),
        'hours': fields.function(_get_hours, type='one2many', relation='account.analytic.line', method=True, string="Hours", size=64)
        }

project_project()

class Wiki(osv.osv):
    _inherit = "wiki.wiki"
    _columns = {
        'project_id': fields.many2one('project.project', 'Project')
        }

    def write(self, cr, uid, ids, vals, context={}):
        wiki = self.browse(cr, uid, ids[0])
        res = super(Wiki, self).write(cr, uid, ids, vals, context={})
        cr.commit()
        task_data = self.browse(cr, uid, ids[0], context)
        desc = '''Hello,\n\n  The wiki information is updated for the project: %s\n\nModified Datas are:\n''' %(str(wiki.project_id.name),)
        for val in vals:
            if val.endswith('id') or val.endswith('ids'):
                continue
            desc += '========\n' +val + ':' + str(vals[val]) + "\n"
        desc += '\nThanks,\n' + 'Project Manager\n' + (task_data.project_id.manager and task_data.project_id.manager.name) or ''
        self.pool.get('project.project')._log_event(cr, uid, wiki.project_id.id, {
                                                                'res_id' : ids[0],
                                                                'name' : wiki.name or '',
                                                                'description' : desc,
                                                                'user_id': uid,
                                                                'action' : 'write',
                                                                'type' : 'task'})
        return res

Wiki()

class crm_case(osv.osv):
    _inherit = 'crm.case'

    def _get_latest_cases(self, cr, uid, ids_cases, name, args, context={}):
        if not ids_cases:
            return {}
        result = {}
        for id in ids_cases:
            result[id] = {
                  'bug_ids': '',
                  'feature_ids': '',
                  'support_ids': '',
                  'announce_ids': '',
                          }

        date_back = datetime.date.today() +  datetime.timedelta(days=-31)
        date_back = date_back.strftime('%Y-%m-%d')

        if context.has_key('project_id') and context['project_id']:
            project_id = context['project_id']
        else:
            project_ids = self.pool.get('project.project').search(cr, uid, [('manager', '=', uid)])
            project_id = project_ids and project_ids[0]

        for case in self.browse(cr, uid, ids_cases, context):
            cr.execute("""select c.id from crm_case c left join project_project p on p.id = c.project_id \
                        where c.section_id = p.section_bug_id and c.date >= %s and p.id=%s """, (date_back,project_id,))
            list_case = map(lambda x: x[0], cr.fetchall())
            result[case.id]['bug_ids'] = list_case

            cr.execute("""select c.id from crm_case c left join project_project p on p.id = c.project_id \
                        where c.section_id = p.section_feature_id and c.date >= %s and p.id=%s """, (date_back, project_id,))
            list_case = map(lambda x: x[0], cr.fetchall())
            result[case.id]['feature_ids'] = list_case

            cr.execute("""select c.id from crm_case c left join project_project p on p.id = c.project_id \
                        where c.section_id = p.section_support_id and c.date >= %s and p.id=%s """, (date_back, project_id,))
            list_case = map(lambda x: x[0], cr.fetchall())
            result[case.id]['support_ids'] = list_case

            cr.execute("""select c.id from crm_case c left join project_project p on p.id = c.project_id \
                        where c.section_id = p.section_annouce_id and c.date >= %s and p.id=%s """, (date_back, project_id,))
            list_case = map(lambda x: x[0], cr.fetchall())
            result[case.id]['announce_ids'] = list_case
        return result

    _columns = {
        'bug_ids' : fields.function(_get_latest_cases,type='one2many', relation='crm.case', method=True , string= 'Latest Bugs', multi='case'),
        'feature_ids' : fields.function(_get_latest_cases,type='one2many', relation='crm.case', method=True , string='Latest Features', multi='case'),
        'support_ids' : fields.function(_get_latest_cases,type='one2many', relation='crm.case', method=True , string='Latest Supports', multi='case'),
        'announce_ids' : fields.function(_get_latest_cases,type='one2many', relation='crm.case', method=True , string= 'Latest Announces', multi='case'),
        'project_id': fields.many2one('project.project', 'Project')
     }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('project_id') and context['project_id']:
            project_id = context['project_id']
        else:
            project_ids = self.pool.get('project.project').search(cr, uid, [('manager', '=', uid)])
            project_id = project_ids and project_ids[0]
        if context.has_key('section') and context['section']=='Bug Tracking' or context.has_key('case_search') and context['case_search']=='bug':
            cr.execute('select c.id from crm_case c left join project_project p on p.id=c.project_id \
                        where c.section_id=p.section_bug_id and p.id=%s',(project_id,))
            return map(lambda x: x[0], cr.fetchall())
        elif context.has_key('section') and context['section']=='Feature' or context.has_key('case_search') and context['case_search']=='feature':
            cr.execute('select c.id from crm_case c left join project_project p on p.id=c.project_id \
                        where c.section_id=p.section_feature_id and p.id=%s',(project_id,))
            return map(lambda x: x[0], cr.fetchall())
        elif context.has_key('section') and context['section']=='Support' or context.has_key('case_search') and context['case_search']=='support':
            cr.execute('select c.id from crm_case c left join project_project p on p.id=c.project_id \
                        where c.section_id=p.section_support_id and p.id=%s',(project_id,))
            return map(lambda x: x[0], cr.fetchall())
        elif context.has_key('section') and context['section']=='Announce' or context.has_key('case_search') and context['case_search']=='announce':
            cr.execute('select c.id from crm_case c left join project_project p on p.id=c.project_id \
                        where c.section_id=p.section_annouce_id and p.id=%s',(project_id,))
            return map(lambda x: x[0], cr.fetchall())
        return super(crm_case, self).search(cr, uid, args, offset, limit, order, context, count)

    def create(self, cr, uid, values, context={}): # to be check
        res = super(crm_case, self).create(cr, uid, values, context=context)
        cr.commit()
        case = self.browse(cr, uid, res, context=context)
        case = case[0]
        if case.project_id:
            desc = ''' Hello, \n \t The new case is created for the Project: %s \n\n And its Details are: \n \n Case: %s \n Created on: %s \n Responsible: %s \n Deadline: %s \n Section: %s \n For Partner: %s \n Case Summary: \n ====== \n %s \n \n ======= \n \nThanks,\nProject Manager \n%s''' \
                       %(case.project_id.name,\
                         case.name, case.create_date, case.user_id.name, \
                         case.date_deadline or '', case.section_id.name, \
                         case.partner_id and case.partner_id.name or '',\
                         case.description or '',case.project_id.manager and case.project_id.manager.name or '')
            self.pool.get('project.project')._log_event(cr, uid, case.project_id.id, {
                                'res_id' : case.id,
                                'name' : case.name,
                                'description' : desc,
                                'user_id': uid,
                                'action' : 'create',
                                'type' : 'case'})
        return res

    def write(self, cr, uid, ids, vals, context={}):
        res = super(crm_case, self).write(cr, uid, ids, vals, context={})
        cr.commit()
        case_data = self.browse(cr, uid, ids[0], context)
        case_data = case_data[0]
        desc = '''Hello ,\n\n  The case is updated for the project: %s\n\nModified Datas are:\n''' %(str(case_data.project_id.name),)
        for val in vals:
            if val.endswith('id') or val.endswith('ids'):
                continue
            desc += val + ':' + str(vals[val]) + "\n"
        if case_data.project_id:
            desc += '\nThanks,\n' + 'Project Manager\n' + (case_data.project_id and case_data.project_id.manager and case_data.project_id.manager.name or False)
            self.pool.get('project.project')._log_event(cr, uid, case_data.project_id.id, {
                                                                'res_id' : ids[0],
                                                                'name' : case_data.name or '',
                                                                'description' : desc,
                                                                'user_id': uid,
                                                                'action' : 'write',
                                                                'type' : 'case'})
        return res

crm_case()

class report_account_analytic_planning(osv.osv):
    _inherit = 'report_account_analytic.planning'
    _description = "Planning of tasks related portal project"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('portal_gantt') and context['portal_gantt'] == 'planning' and context.has_key('active_id') and context['active_id']:
            cr.execute("""select rp.id from report_account_analytic_planning rp where rp.id in \
                            (select planning_line_id from project_task where project_id in \
                            (select id from project_project where id = %s))""" %(context['active_id']))
            return map(lambda x: x[0], cr.fetchall())
        return super(report_account_analytic_planning, self).search(cr, uid, args, offset, limit, order, context, count)

report_account_analytic_planning()

class ir_attachment(osv.osv):
     _inherit = 'ir.attachment'
     _description = 'Attachments related project and task'

     def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
         prj_model = 'project.project'
         task_model = 'project.task'
         if context is None:
             context = {}
         if context.has_key('portal_attachment') and context['portal_attachment'] == 'attachment' and context.has_key('project_activeid') and context['project_activeid']:
             cr.execute("""select i.id from project_project as p left join ir_attachment as i on i.res_id=p.id \
                             where p.id=%s and i.res_model=%s""", (context['project_activeid'],prj_model))
             prj_attach_ids = map(lambda x: x[0], cr.fetchall())
             cr.execute("""select i.id from project_task t left join project_project p \
                            on p.id=t.project_id left join ir_attachment i on i.res_id=t.id \
                            where p.id=%s and i.res_model=%s""", (context['project_activeid'],task_model))
             task_attach_ids = map(lambda x: x[0], cr.fetchall())
             return prj_attach_ids + task_attach_ids
         return super(ir_attachment, self).search(cr, uid, args, offset, limit, order, context, count)

ir_attachment()

class hr_timesheet_sheet(osv.osv):
    _inherit = 'hr_timesheet_sheet.sheet'
    _description = "Timesheet related portal project"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('portal_sheet') and context['portal_sheet'] == 'timesheet' and context.has_key('project_activeid') and context['project_activeid']:
            cr.execute("select aal.id from account_analytic_line aal, hr_analytic_timesheet hat \
                        where hat.id = aal.id and aal.account_id in (select category_id from \
                        project_project where id = %s)" %context['project_activeid'])
            line_ids = map(lambda x: x[0], cr.fetchall())
            sheet = self.pool.get('hr.analytic.timesheet').read(cr, uid, line_ids, ['sheet_id'])
            return list(set(map(lambda x:x['sheet_id'][0], sheet)))
        return super(hr_timesheet_sheet, self).search(cr, uid, args, offset, limit, order, context, count)

hr_timesheet_sheet()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _description = "Invoices related portal project"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('portal_invoice') and context['portal_invoice'] == 'invoice' and context.has_key('project_activeid') and context['project_activeid']:
            cr.execute("""select id from account_invoice_line where account_analytic_id in \
                        (select category_id from project_project where id = %s)""" %(context['project_activeid']))
            invoice_line_ids = map(lambda x: x[0], cr.fetchall())
            invoice = self.pool.get('account.invoice.line').read(cr, uid, invoice_line_ids, ['invoice_id'])
            return list(set(map(lambda x:x['invoice_id'][0], invoice)))
        return super(account_invoice, self).search(cr, uid, args, offset, limit, order, context, count)

account_invoice()

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    _description = "Analytic accounts with analysis summary related portal project"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('portal_account') and context['portal_account'] == 'financial' and context.has_key('project_activeid') and context['project_activeid']:
            cr.execute("""select id from account_analytic_account where id in (select category_id from \
                            project_project where id = %s)""" %(context['project_activeid']))
            return map(lambda x: x[0], cr.fetchall())
        return super(account_analytic_account, self).search(cr, uid, args, offset, limit, order, context, count)

account_analytic_account()

class report_crm_case_bugs(osv.osv):
    _name = "report.crm.case.bugs"
    _description = "Bugs by state & user"
    _auto = False
    _rec_name = 'user_id'
    _columns = {
        'nbr': fields.integer('# of Cases', readonly=True),
        'state': fields.selection(AVAILABLE_STATES, 'Status', size=16, readonly=True),
        'user_id': fields.many2one('res.users', 'User', size=16, readonly=True),
        'project_id' : fields.many2one('project.project', 'Project', size=64),
        'section_id' : fields.many2one('crm.case.section', 'Section', required=False)
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('bugs_user') and context['bugs_user']=='bug_form' and context.has_key('project_id') and context['project_id']:
            cr.execute('select id from report_crm_case_bugs where project_id=%s',(context['project_id']))
            return map(lambda x: x[0], cr.fetchall())
        return super(report_crm_case_bugs, self).search(cr, uid, args, offset, limit, order, context, count)

    def init(self, cr):
        cr.execute("""
            create or replace view report_crm_case_bugs as (
                select
                    min(c.id) as id,
                    c.user_id,
                    c.project_id as project_id,
                    c.section_id as section_id,
                    count(*) as nbr,
                    c.state
                from
                    crm_case c
                    left join project_project p on p.id = c.project_id
                where c.section_id = p.section_bug_id
                group by c.user_id, c.project_id, c.section_id, c.state
            )""")


report_crm_case_bugs()

class report_crm_case_features_user(osv.osv):
    _name = "report.crm.case.features.user"
    _description = "Features by User"
    _auto = False
    _rec_name = 'user_id'
    _columns = {
        'nbr': fields.integer('# of Cases', readonly=True),
        'user_id': fields.many2one('res.users', 'User', size=16, readonly=True),
        'project_id': fields.many2one('project.project', 'Project')
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('project_id') and context['project_id']:
            cr.execute('select id from report_crm_case_features_user where project_id=%s',(context['project_id']))
            return map(lambda x: x[0], cr.fetchall())
        return super(report_crm_case_features_user, self).search(cr, uid, args, offset, limit, order, context, count)


    def init(self, cr):
        cr.execute("""
            create or replace view report_crm_case_features_user as (
                select
                    min(c.id) as id,
                    c.user_id,
                    count(*) as nbr,
                    p.id as project_id
                from
                    crm_case c
                    left join project_project p on p.id = c.project_id
                where c.section_id = p.section_feature_id
                group by c.user_id, c.name, p.id
            )""")


report_crm_case_features_user()

class report_crm_case_support_user(osv.osv):
    _name = "report.crm.case.support.user"
    _description = "Support by User"
    _auto = False
    _rec_name = 'user_id'
    _columns = {
        'nbr': fields.integer('# of Cases', readonly=True),
        'user_id': fields.many2one('res.users', 'User', size=16, readonly=True),
        'project_id': fields.many2one('project.project', 'Project')
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('project_id') and context['project_id']:
            cr.execute('select id from report_crm_case_support_user where project_id=%s',(context['project_id']))
            return map(lambda x: x[0], cr.fetchall())
        return super(report_crm_case_support_user, self).search(cr, uid, args, offset, limit, order, context, count)

    def init(self, cr):
        cr.execute("""
            create or replace view report_crm_case_support_user as (
                select
                    min(c.id) as id,
                    c.user_id,
                    count(*) as nbr,
                    p.id as project_id
                from
                    crm_case c
                    left join project_project p on p.id = c.project_id
                where c.section_id = p.section_support_id
                group by c.user_id, c.name, p.id
            )""")


report_crm_case_support_user()

class report_crm_case_announce_user(osv.osv):
    _name = "report.crm.case.announce.user"
    _description = "Announces by User"
    _auto = False
    _rec_name = 'user_id'
    _columns = {
        'name': fields.char('Description',size=64,required=True),
        'nbr': fields.integer('# of Cases', readonly=True),
        'user_id': fields.many2one('res.users', 'User', size=16, readonly=True),
        'project_id': fields.many2one('project.project', 'Project')
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.has_key('project_id') and context['project_id']:
            cr.execute('select id from report_crm_case_announce_user where project_id=%s',(context['project_id']))
            return map(lambda x: x[0], cr.fetchall())
        return super(report_crm_case_announce_user, self).search(cr, uid, args, offset, limit, order, context, count)

    def init(self, cr):
        cr.execute("""
            create or replace view report_crm_case_announce_user as (
                select
                    min(c.id) as id,
                    c.user_id,
                    c.name as name,
                    count(*) as nbr,
                    p.id as project_id
                from
                    crm_case c
                    left join project_project p on p.id = c.project_id
                where c.section_id = p.section_annouce_id
                group by c.user_id, c.name, p.id
            )""")


report_crm_case_announce_user()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2008-2009 Syleam (<http://syleam.fr>). All Rights Reserved
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

from osv import osv
from osv import fields
from tools.translate import _
from tools import ustr
from math import ceil

import time

class crm_case_work(osv.osv):
    _name = 'crm.case.work'
    _description = 'CRM summary work'

    _columns = {
        'case_id': fields.many2one('crm.case', 'Case', ondelete='cascade', required=True),
        'name': fields.char('Work summary', size=128),
        'date': fields.datetime('Date'),
        'hours': fields.float('Time spent'),
        'user_id': fields.many2one('res.users', 'Done by', required=True),
        'hr_analytic_timesheet_id':fields.integer('Related Timeline Id'),
    }

    _defaults = {
        'user_id': lambda obj,cr,uid,context: uid,
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _order = "date desc"


    def _get_analytic_account_id(self, cr, uid, vals, context=None):
        """
        Return account ; try to find it based on case values
        This methode can be overload to replace account number
        """
        obj_case = self.pool.get('crm.case').browse(cr, uid, vals['case_id'])
        if obj_case.analytic_account_id:
            out_account_id = obj_case.analytic_account_id.id
        else:
            out_account_id = False
            if obj_case.partner_id:
                pa_obj = self.pool.get('res.partner.crm.analytic')
                dm = [
                    ('partner_id','=',obj_case.partner_id.id),
                    ('section_id','=',obj_case.section_id.id),
                ]
                an_id = pa_obj.search(cr, uid, dm)
                if an_id:
                    acc_id = pa_obj.read(cr, uid, an_id[0])
                    if acc_id.get('account_id', False):
                        out_account_id = acc_id['account_id'][0]

            if not out_account_id:
                if obj_case.section_id.req_partner:
                    raise osv.except_osv(_('Error !'),
                        _('Analytic account must be defined on partner !'))

                if not obj_case.section_id.account_id:
                    raise osv.except_osv(_('Bad Configuration !'),
                        _('No default analytic account on this section !'))

                out_account_id = obj_case.section_id.account_id.id
        return out_account_id


    def _get_analytic_account_name(self, cr, uid, vals, case_id=None, context=None):
        """
        Return label for line of analytic account (based on case values)
        Actualy prefix with crm.case name
        """
        if not context: context = {}
        if not case_id:
            case_id = vals['case_id']
        obj_case = self.pool.get('crm.case').browse(cr, uid, case_id)
        if vals['name']:
            ts_name = '%s: %s' % (ustr(obj_case.name[:64]), ustr(vals['name'][:62]))
        else:
            ts_name = ustr(obj_case.name[:126]) + ' /'
        return ts_name


    def create(self, cr, uid, vals, *args, **kwargs):
        obj = self.pool.get('hr.analytic.timesheet')
        vals_line = {}
        emp_obj = self.pool.get('hr.employee')
        emp_id = emp_obj.search(cr, uid, [('user_id', '=', vals.get('user_id', uid))])

        if not emp_id:
            raise osv.except_osv(_('Bad Configuration !'),
                 _('No employee defined for this user. You must create one.'))
        emp = self.pool.get('hr.employee').browse(cr, uid, emp_id[0])
        if not emp.product_id:
            raise osv.except_osv(_('Bad Configuration !'),
                 _('No product defined on the related employee.\nFill in the timesheet tab of the employee form.'))

        if not emp.journal_id:
            raise osv.except_osv(_('Bad Configuration !'),
                 _('No journal defined on the related employee.\nFill in the timesheet tab of the employee form.'))

        vals_line['account_id'] = self._get_analytic_account_id(cr, uid, vals)

        a =  emp.product_id.product_tmpl_id.property_account_expense.id
        if not a:
            a = emp.product_id.categ_id.property_account_expense_categ.id
        vals_line['general_account_id'] = a
        vals_line['journal_id'] = emp.journal_id.id
        vals_line['name'] = self._get_analytic_account_name(cr, uid, vals)
        vals_line['user_id'] = vals['user_id']
        vals_line['date'] = vals['date'][:10]
        vals_line['unit_amount'] = vals['hours']
        vals_line['amount'] = 00.0
        vals_line['product_id'] = emp.product_id and emp.product_id.id or False
        timeline_id = obj.create(cr, uid, vals_line, {})

        vals_line['amount'] = (-1) * vals['hours'] * obj.browse(cr, uid, timeline_id).product_id.standard_price
        obj.write(cr, uid,[timeline_id], vals_line, {})
        vals['hr_analytic_timesheet_id'] = timeline_id
        return super(crm_case_work,self).create(cr, uid, vals, *args, **kwargs)

    def write(self, cr, uid, ids, vals, context=None):
        if not context: context = {}
        vals_line = {}

        for case in self.pool.get('crm.case.work').browse(cr, uid, ids):
            line_id = vals.get('hr_analytic_timesheet_id',case.hr_analytic_timesheet_id)
            if line_id:
                obj = self.pool.get('hr.analytic.timesheet')
                if 'name' in vals:
                    vals_line['name'] = self._get_analytic_account_name(cr, uid, vals, case_id=case.case_id.id)
                if 'user_id' in vals:
                    vals_line['user_id'] = vals['user_id']
                if 'date' in vals:
                    vals_line['date'] = vals['date'][:10]
                if 'hours' in vals:
                    vals_line['unit_amount'] = vals['hours']
                    vals_line['amount'] = (-1) * vals['hours'] * obj.browse(cr, uid, line_id).product_id.standard_price
                obj.write(cr, uid, [line_id], vals_line, {})

        return super(crm_case_work,self).write(cr, uid, ids, vals, context)


    def unlink(self, cr, uid, ids, *args, **kwargs):
        """
        When line was removed, the analytic line must be remove to
        """
        for ts in self.pool.get('crm.case.work').browse(cr, uid, ids):
            if ts.hr_analytic_timesheet_id:
                obj = self.pool.get('hr.analytic.timesheet').unlink(cr, uid, [ts.hr_analytic_timesheet_id], *args, **kwargs)
        return super(crm_case_work,self).unlink(cr, uid, ids, *args, **kwargs)

crm_case_work()

class crm_case(osv.osv):
    _inherit = 'crm.case'

    _columns = {
        'timesheet_ids': fields.one2many('crm.case.work', 'case_id', 'Summary Work'),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Contract', help='Link to an Analytic Account'),
    }

    def create(self, cr, uid, vals, context=None):
        """
        If calculate_duration is pass on the context or indicate in section, all time enter on the crm.case.work
        are sum and save it on duration field
        """
        if context is None:
            context = {}
        if context.get('calculate_duration', False) or (vals.get('section_id', False) and self.pool.get('crm.case.section').read(
                cr, uid, vals['section_id'], ['calculate_duration'], context=context
                )['calculate_duration']):
            if vals.get('timesheet_ids', False):
                duration = 0.0
                for t in vals['timesheet_ids']:
                    if t[2]:
                        # Add hours of timesheet modified
                        duration += t[2]['hours']
                vals['duration'] = duration
        return super(crm_case, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        If calculate_duration is pass on the context or indicate in section, all time enter on the crm.case.work
        are sum and save it on duration field
        """
        if not context:
            context = {}
        for case in self.browse(cr, uid, ids, context=context):
            if context.get('calculate_duration', False) or case.section_id.calculate_duration:
                crm_case_work_obj = self.pool.get('crm.case.work')
                unlink_ids = []
                write_ids = []
                if vals.get('timesheet_ids', False):
                    for z in vals['timesheet_ids']:
                        if not z[2]:
                            # check if this timesheet is to unlink
                            unlink_ids.append(z[1])
                        elif z[1]:
                            # check if this timesheet is to modify
                            write_ids.append(z[1])
                duration = 0.0
                for c in case.timesheet_ids:
                    if c.id not in unlink_ids and c.id not in write_ids:
                        # Add hours for timesheet not unlinked or modified
                        duration += c.hours
                if vals.get('timesheet_ids', False):
                    for t in vals['timesheet_ids']:
                        if t[2]:
                            # Add hours of timesheet modified
                            duration += t[2]['hours']
                vals_case_id = {}
                vals_case_id['case_id'] = case.id
                account_id = crm_case_work_obj._get_analytic_account_id(cr, uid, vals_case_id, context)
                account_analytic_obj = self.pool.get('account.analytic.account')
                if account_id:
                    rounding = account_analytic_obj.read(cr, uid, account_id, ['rounding_duration'])['rounding_duration']
                    if rounding:
                        # Rounding duration
                        duration = ceil((duration * 100) / (rounding * 100)) * rounding
                vals['duration'] = duration
        return super(crm_case, self).write(cr, uid, ids, vals, context)

crm_case()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

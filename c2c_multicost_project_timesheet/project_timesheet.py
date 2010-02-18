# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camtocamp SA
# @author Joël Grand-Guillaume
# $Id: $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from osv import fields, osv
import time
import datetime
import pooler
import tools
from tools.translate import _


class project_work(osv.osv):
    _inherit = "project.task.work"
    _description = "Task Work"
        
    def create(self, cr, uid, vals, *args, **kwargs):
        obj = self.pool.get('hr.analytic.timesheet')
        vals_line = {}
        obj_task = self.pool.get('project.task').browse(cr, uid, vals['task_id'])
        result = self.get_user_related_details(cr, uid, vals.get('user_id', uid))
        vals_line['name'] = '%s: %s' % (tools.ustr(obj_task.name), tools.ustr(vals['name']) or '/')
        vals_line['user_id'] = vals['user_id']
        vals_line['product_id'] = result['product_id']
        vals_line['date'] = vals['date'][:10]
        vals_line['unit_amount'] = vals['hours']
        acc_id = obj_task.project_id.category_id.id
        vals_line['account_id'] = acc_id
        res = obj.on_change_account_id(cr, uid, False, acc_id)
        if res.get('value'):
            vals_line.update(res['value'])
        vals_line['general_account_id'] = result['general_account_id']
        vals_line['journal_id'] = result['journal_id']
        vals_line['amount'] = 00.0
        vals_line['product_uom_id'] = result['product_uom_id']
        timeline_id = obj.create(cr, uid, vals_line, {})

        # Compute based on pricetype
        amount_unit=obj.on_change_unit_amount(cr, uid, line_id, 
            vals_line['product_id'], vals_line['unit_amount'], unit, context)
        
        vals_line['amount'] = (-1) * vals['hours']* (unit_amount or 0.0)
        
        obj.write(cr, uid,[timeline_id], vals_line, {})
        vals['hr_analytic_timesheet_id'] = timeline_id
        return super(project_work,self).create(cr, uid, vals, *args, **kwargs)

    def write(self, cr, uid, ids, vals, context=None):
        vals_line = {}

        task = self.pool.get('project.task.work').browse(cr, uid, ids)[0]
        line_id = task.hr_analytic_timesheet_id
        # in case,if a record is deleted from timesheet,but we change it from tasks!
        list_avail_ids = self.pool.get('hr.analytic.timesheet').search(cr, uid, [])
        if line_id in list_avail_ids:
            obj = self.pool.get('hr.analytic.timesheet')
            if 'name' in vals:
                vals_line['name'] = '%s: %s' % (tools.ustr(task.task_id.name), tools.ustr(vals['name']) or '/')
            if 'user_id' in vals:
                vals_line['user_id'] = vals['user_id']
                result = self.get_user_related_details(cr, uid, vals['user_id'])
                vals_line['product_id'] = result['product_id']
                vals_line['general_account_id'] = result['general_account_id']
                vals_line['journal_id'] = result['journal_id']
                vals_line['product_uom_id'] = result['product_uom_id']
            if 'date' in vals:
                vals_line['date'] = vals['date'][:10]
            if 'hours' in vals:
                vals_line['unit_amount'] = vals['hours']
                # Compute based on pricetype
                amount_unit=obj.on_change_unit_amount(cr, uid, line_id, 
                     vals_line['product_id'], vals_line['unit_amount'], unit, context)
               
                vals_line['amount'] = (-1) * vals['hours'] * (amount_unit or 0.0)

            obj.write(cr, uid, [line_id], vals_line, {})

        return super(project_work,self).write(cr, uid, ids, vals, context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


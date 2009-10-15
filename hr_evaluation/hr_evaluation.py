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
from osv import fields, osv

class hr_evaluation(osv.osv):
    _name = "hr_evaluation.evaluation"
    _description = "Employee Evaluation"
    _columns = {
        'name': fields.char("Summary", size=64, required=True),
        'date': fields.date("Date", required=True),
        'employee_id': fields.many2one("hr.employee", "Employee", required=True),
        'user_id': fields.many2one("res.users", "Evaluation User", required=True),
        'info_good': fields.text('Good Points'),
        'info_bad': fields.text('Bad Points'),
        'info_improve': fields.text('To Improve'),
        'score': fields.float("Score"),
        'info_employee': fields.text('Employee Response'),
        'quote_ids': fields.one2many('hr_evaluation.quote', 'evaluation_id', 'Quotes'),
        'state': fields.selection([('draft','Draft'),('done','Done')], 'State')
    }
    _defaults = {
        'date' : lambda *a: time.strftime('%Y-%m-%d'),
        'state' : lambda *a: 'draft',
        'user_id' : lambda self,cr,uid,context={}: uid
    }
hr_evaluation()

class hr_evaluation_type(osv.osv):
    _name = "hr_evaluation.type"
    _description = "Employee Evaluation Type"
    _columns = {
        'name': fields.char("Evaluation Criterion", size=64, required=True),
        'category_ids': fields.many2many('hr.employee.category', 'hr_evaluation_category_rel', 'type_id', 'category_id', 'Appliable Role'),
        'active': fields.boolean("Active"),
        'value_ids': fields.one2many('hr_evaluation.type.value', 'type_id', 'Values'),
        'info': fields.text('Information'),
        'score': fields.float('Score'),
    }
    _defaults = {
        'active' : lambda *a: True,
    }
hr_evaluation_type()

class hr_evaluation_type_value(osv.osv):
    _name = "hr_evaluation.type.value"
    _description = "Evaluation Type Value"
    _columns = {
        'name': fields.char("Value", size=64, required=True),
        'score': fields.float("Score"),
        'type_id': fields.many2one('hr_evaluation.type', 'Evaluation Type', required=True),
    }
hr_evaluation_type_value()

class hr_evaluation_quote(osv.osv):
    _name = "hr_evaluation.quote"
    _description = "Employee Evaluation Quote"
    _columns = {
        'name': fields.char("Quote", size=64),
        'type_id': fields.many2one('hr_evaluation.type', 'Type'),
        'score': fields.float("Score"),
        'value_id': fields.many2one('hr_evaluation.type.value', 'Value', domain="[('type_id','=',type_id)])"),
        'evaluation_id': fields.many2one('hr_evaluation.evaluation', 'Evaluation', required=True)
    }
hr_evaluation_quote()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


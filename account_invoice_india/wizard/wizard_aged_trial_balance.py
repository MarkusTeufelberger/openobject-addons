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
import wizard
import time
import datetime
import pooler
import mx.DateTime
from mx.DateTime import *

_aged_trial_form = """<?xml version="1.0"?>
<form string="Aged Trial Balance">
	<field name="company_id"/>
	<newline/>
	<field name="fiscalyear"/>
	<newline/>
	<field name="date_from" />
    <field name="date_to"/>
    <field name="partners" colspan="4"/>
	<field name="period_length"/>
</form>"""

_aged_trial_fields = {
	'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
	'fiscalyear': {'string': 'Fiscal year', 'type': 'many2one', 'relation': 'account.fiscalyear',
		'help': 'Keep empty for all open fiscal year'},
	'period_length': {'string': 'Period length (days)', 'type': 'integer', 'required': True, 'default': lambda *a:30},
	'date_from': {'string':"Start date",'type':'date','required':True ,'default': lambda *a: time.strftime('%Y-01-01')},
    'date_to': {'string':"End date",'type':'date','required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
    'partners': {'string': 'Partners', 'type': 'many2many', 'relation': 'res.partner', 'help': 'All Partners if empty'}
}

def _calc_dates(self, cr, uid, data, context):
	res = {}
	period_length = data['form']['period_length']
	if period_length<=0:
		raise wizard.except_wizard('UserError', 'You must enter a period length that cannot be 0 or below !')
	start = mx.DateTime.strptime(data['form']['date_to'], '%Y-%m-%d')
	for i in range(5)[::-1]:
		stop = start-RelativeDateTime(days=period_length)
		end_date = mx.DateTime.strptime(data['form']['date_from'], '%Y-%m-%d')
		if stop < end_date:
			stop = end_date
			res[str(i)] = {
			'name' : 'over '+str((5-i)*period_length)+' days',
			'stop': end_date.strftime('%Y-%m-%d'),
			'start' : end_date.strftime('%Y-%m-%d'),
		}
			start = end_date
		else :
			res[str(i)] = {
				'name' : 'over '+str((5-i)*period_length)+' days',
				'stop': start.strftime('%Y-%m-%d'),
				'start' : stop.strftime('%Y-%m-%d'),
			}
			start = stop - RelativeDateTime(days=1)
	return res

class wizard_report(wizard.interface):
	def _get_defaults(self, cr, uid, data, context):
		fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
		data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)

		user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
		if user.company_id:
			company_id = user.company_id.id
		else:
			company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
		data['form']['company_id'] = company_id

		return data['form']


	states = {
		'init': {
			'actions': [_get_defaults],
			'result': {'type':'form', 'arch':_aged_trial_form, 'fields':_aged_trial_fields, 'state':[('end','Cancel'),('print','Print Aged Trial Balance')]},
		},
		'print': {
			'actions': [_calc_dates],
			'result': {'type':'print', 'report':'account.aged.trial.balance1', 'state':'end'},
		},
	}

wizard_report('account.aged.trial.balance1')


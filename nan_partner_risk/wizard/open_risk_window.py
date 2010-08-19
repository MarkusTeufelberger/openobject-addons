# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009 Albert Cervera i Areny (http://www.nan-tic.com). All Rights Reserved
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

import wizard
import pooler

view_form = """<?xml version="1.0"?>
<form string="Risk Information">
	<field name="unpayed_amount" colspan="4"/>
	<field name="pending_amount" colspan="4"/>
	<field name="draft_invoices_amount" colspan="4"/>
	<field name="circulating_amount" colspan="4"/>
	<field name="pending_orders_amount" colspan="4"/>
    <separator colspan="4"/>
	<field name="total_debt" colspan="4"/>
    <label string="" colspan="4"/>
	<field name="credit_limit" colspan="4"/>
	<field name="available_risk" colspan="4"/>
	<field name="total_risk_percent" widget="progressbar" colspan="4"/>
</form>
"""

view_fields = {
	'unpayed_amount': { 'string': 'Expired Unpaid Payments', 'type': 'float', 'readonly': True },
	'pending_amount': { 'string': 'Unexpired Pending Payments', 'type': 'float', 'readonly': True },
	'draft_invoices_amount': { 'string': 'Draft Invoices', 'type': 'float', 'readonly': True },
	'circulating_amount': { 'string': 'Payments Sent to Bank', 'type': 'float', 'readonly': True },
	'pending_orders_amount': { 'string': 'Uninvoiced Orders', 'type': 'float', 'readonly': True },
	'total_debt': { 'string': 'Total Debt', 'type': 'float', 'readonly': True },
	'credit_limit': { 'string': 'Credit Limit', 'type': 'float', 'readonly': True },
	'available_risk': { 'string': 'Available Credit', 'type': 'float', 'readonly': True },
	'total_risk_percent': { 'string': 'Credit Usage (%)', 'type': 'float', 'readonly': True },
}


class open_risk_window(wizard.interface):

	def _action_open_window(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		if data['ids']:
			id = data['ids'][0]
		else:
			id = 0
		res = pool.get('res.partner').read( cr, uid, id, view_fields.keys() )
		return res

	states = {
		'init': {
			'actions': [_action_open_window],
			'result': {
				'type': 'form',
				'arch': view_form,
				'fields': view_fields,
				'state': [('end','Close','gtk-close')]
			}
		}
	}
open_risk_window('open_risk_window')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

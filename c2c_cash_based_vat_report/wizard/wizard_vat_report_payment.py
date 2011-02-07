# -*- encoding: utf-8 -*-
#
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
##############################################################################
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


import time
import wizard
import pooler

dates_form = '''<?xml version="1.0"?>
<form string="Select period">
	<field name="company_id"/>
	<newline/>
	<field name="date_from"/>
	<field name="date_to"/>
	<field name="date_to_from"/>


</form>'''

dates_fields = {
	'company_id': {'string': 'Company', 'type': 'many2one',
		'relation': 'res.company', 'required': True},
        'date_from': {'string':'        Start date', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('2010-04-01')},
        'date_to': {'string':'End date', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('2010-12-31')},
        'date_to_from': {'string':'Select date that you want to control in detailed vat report', 'type':'selection','selection':[('date_from','Start date'),('date_to','End Date')],'required':True, 'default': lambda *args:'date_to'},

}



class wizard_vat_report(wizard.interface):

        def _account_chart_open_window(self, cr, uid, data, context):
            mod_obj = pooler.get_pool(cr.dbname).get('ir.model.data')
            act_obj = pooler.get_pool(cr.dbname).get('ir.actions.act_window')

            result = mod_obj._get_id(cr, uid, 'c2c_vat_report_payment', 'action_vat_mod_tree')
            id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
            result = act_obj.read(cr, uid, [id], context=context)[0]
            result['context'] = str({'date_from': data['form']['date_from'],'date_to':data['form']['date_to'],'company_id':data['form']['company_id']})
            if data['form']['date_from'] and data['form']['date_to']:
                result['name']+=':'+ str(data['form']['date_from']) + '-' +  str(data['form']['date_to'])
            return result



	def _get_defaults(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		user = pool.get('res.users').browse(cr, uid, uid, context=context)
		if user.company_id:
			company_id = user.company_id.id
		else:
			company_id = pool.get('res.company').search(cr, uid,
					[('parent_id', '=', False)])[0]
		data['form']['company_id'] = company_id

		return data['form']

	states = {
		'init': {
			'actions': [_get_defaults],
			'result': {
				'type': 'form',
				'arch': dates_form,
				'fields': dates_fields,
				'state': [
					('end', 'Cancel'),
					('view_vat', 'Show VAT Decl.'),
					('report_vat', 'Print VAT Decl.'),
					('report_vat_full', 'Print detailed VAT Decl.')
				]
			}
		},
		'view_vat': {
                        'actions': [],
                        'result': {'type': 'action', 'action':_account_chart_open_window, 'state':'end'}
		},
		'report_vat': {
                        'actions': [],
                        'result': {'type':'print', 'report':'account.vat.payment.declaration', 'state':'end'}
                },
		'report_vat_full': {
                        'actions': [],
                        'result': {'type':'print', 'report':'account.vat.payment.declaration.full', 'state':'end'}
                }
	}

wizard_vat_report('account_vat_report')
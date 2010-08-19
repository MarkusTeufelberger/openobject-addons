# -*- encoding: utf-8 -*-
# Author OpenERP modified by camptocamp as we can't override wizzard in a simple way
##############################################################################
#
#    OpenERP, Open Source Management Solution	
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
import time
class WizardAccountChart(wizard.interface):
    _account_chart_arch = '''<?xml version="1.0"?>
    <form string="Account charts">
        <field name="fiscalyear"/>
        <label align="0.7" colspan="6" string="(If you do not select Fiscal year it will take all open fiscal years)"/>
        <field name="target_move"/>
        <label align="0.7" colspan="6" string=""/>
        <field name="currency_date"/>
    </form>'''

    _account_chart_fields = {
            'fiscalyear': {
                'string': 'Fiscal year',
                'type': 'many2one',
                'relation': 'account.fiscalyear',
                'help': 'Keep empty for all open fiscal year',
             },
            'target_move': {
                'string': 'Target Moves',
                'type': 'selection',
                'selection': [('all','All Entries'),('posted','All Posted Entries')],
                'required': True,
                'default': lambda *a:"all",
            },
            'currency_date': {
                'string': 'Currency date for consolidated chart',
                'type': 'date',
                'required': True,
                'help': 'If you are looking a consolidated chart the date +\
                 set in this wizzard will be used to retriew the currency',
            },
    }

    def _get_defaults(self, cr, uid, data, context):
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['currency_date'] = time.strftime('%Y-%m-%d')
        return data['form']


    def _account_chart_open_window(self, cr, uid, data, context):
        mod_obj = pooler.get_pool(cr.dbname).get('ir.model.data')
        act_obj = pooler.get_pool(cr.dbname).get('ir.actions.act_window')

        result = mod_obj._get_id(cr, uid, 'account', 'action_account_tree')
        id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['context'] = str({'fiscalyear': data['form']['fiscalyear'],'state':data['form']['target_move'], 'date':data['form']['currency_date']})
        if data['form']['fiscalyear']:
            result['name']+=':'+pooler.get_pool(cr.dbname).get('account.fiscalyear').read(cr,uid,[data['form']['fiscalyear']])[0]['code']
        return result

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type': 'form', 'arch':_account_chart_arch, 'fields':_account_chart_fields, 'state': [('end', 'Cancel'), ('open', 'Open Charts')]}
        },
        'open': {
            'actions': [],
            'result': {'type': 'action', 'action':_account_chart_open_window, 'state':'end'}
        }
    }
WizardAccountChart('account.chart_conso')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


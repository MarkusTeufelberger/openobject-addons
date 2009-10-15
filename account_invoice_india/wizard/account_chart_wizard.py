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
import pooler

class wizard_account_chart(wizard.interface):
    _account_chart_arch = '''<?xml version="1.0"?>
    <form string="Account charts">
        <field name="fiscalyear"/>
        <newline/>
        <field name="periods" colspan="4"/>
    </form>'''
    
    _account_chart_fields = {
        'fiscalyear': {
            'string': 'Fiscal year',
            'type': 'many2one',
            'relation': 'account.fiscalyear',
            'help': 'Keep empty for all open fiscal year',
        },
        'periods': {
            'string': 'Periods',
            'type': 'many2many',
            'relation': 'account.period',
            'help': 'Keep empty for all open fiscal year',
            'domain' : "[('fiscalyear_id','=',fiscalyear)]"
        },
    }

    def _get_defaults(self, cr, uid, data, context):
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        
        periods = pooler.get_pool(cr.dbname).get('account.period')
        ids = periods.search(cr, uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
        
        data['form']['periods'] = ids
        return data['form']

    def _account_chart_open_window(self, cr, uid, data, context):
        mod_obj = pooler.get_pool(cr.dbname).get('ir.model.data')
        act_obj = pooler.get_pool(cr.dbname).get('ir.actions.act_window')

        result = mod_obj._get_id(cr, uid, 'account', 'action_account_tree')
        id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
        result = act_obj.read(cr, uid, [id])[0]
        result['context'] = str({'fiscalyear': data['form']['fiscalyear'],'periods':data['form']['periods'][0][2]})        
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
wizard_account_chart('account.chart.periods')

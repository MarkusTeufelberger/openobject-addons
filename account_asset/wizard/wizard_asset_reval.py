# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import wizard
import pooler
import time
from tools.translate import _

asset_end_arch = '''<?xml version="1.0"?>
<form string="Revaluation">
    <separator string="Revaluation entry" colspan="4"/>
    <field name="period_id"/>
    <field name="date"/>
    <newline/>
    <field name="name" colspan="4"/>
    <field name="acc_impairment" colspan="4"/>
    <field name="value"/>
    <field name="expense_value"/>
    <field name="multiply_value"/>
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'date': {'string': 'Date', 'type': 'date', 'required':True, 'help':"Efective date for accounting move."},
    'period_id': {'string': 'Period', 'type': 'many2one', 'relation':'account.period', 'required':True, 'help':"Calculated period and period for posting."},
    'name': {'string':'Reason', 'type':'char', 'size':64, 'required':True},
    'value': {'string':'Increasing Base Value', 'type':'float', 'help':"Value to be added to method base value. In Direct method it is increasing of book value. In Indirect method it is increasing of cost basis. Negative value means decreasing."},
    'expense_value': {'string':'Increasing Expense Value', 'type':'float', 'help':"Value to be added to asset expenses. Used only in indirect method. In direct method ignored."},
    'multiply_value': {'string':'Multiply Value', 'type':'float', 'help':"Value used as increasing factor for base Value and Expense Value. If you want to increase value by 20% enter 0,2 here. This value can be negative. This field works only if base and expense value are 0."},
    'acc_impairment': {'string':'Impairment Account', 'type': 'many2one', 'relation':'account.account', 'required':True, 'help':"Account for impairment loss amount."},
    'note': {'string':'Notes', 'type':'text'},
}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    method = method_obj.browse(cr, uid, data['id'], context)
    asset_category_id = method.asset_id.asset_category and method.asset_id.asset_category.id or False
    defaults = method_obj.get_defaults(cr, uid, method.method_type.id, asset_category_id, context)
    acc_impairment = defaults and defaults.account_impairment_id and defaults.account_impairment_id.id or False
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    return {
        'note': _("Asset revaluated because: "),
        'acc_impairment': acc_impairment, 
        'date': time.strftime('%Y-%m-%d'),
        'period_id': period_id,
    }

def _asset_reval(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    period_obj = pool.get('account.period')
    period = period_obj.browse(cr, uid, data['form']['period_id'], context)
    method_obj = pool.get('account.asset.method')
    method_obj._check_date(cr, uid, period, data['form']['date'], context)
    method = method_obj.browse(cr, uid, data['id'], context)
    pool.get('account.asset.history').create(cr, uid, {
        'type': "reval",
        'asset_method_id': data['id'],
        'asset_id' : method.asset_id.id,
        'name': data['form']['name'],
#        'method_delay': method.method_delay,
#        'method_period': method.method_period,
        'note': _("Method Revaluation. Last values:") +
                _('\nTotal: ')+ str(method.value_total)+ 
                _('\nResidual: ')+ str(method.value_residual), 
#                _('\nProgressive Factor: ') + str(data['form']['method_progress_factor'])+
#                _('\nSalvage Value: ') + str(data['form']['method_salvage'])+ 
#                _('\nLife Quantity: ') + str(data['form']['life'])+ "\n" + str(data['form']['note']),
    }, context)
    method_obj._post_3lines_move(cr, uid, method, period, data['form']['date'], data['form']['acc_impairment'], data['form']['value'], data['form']['expense_value'], context)
    return {}


class wizard_asset_reval(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_reval','Revaluate')
            ]}
        },
        'asset_reval': {
            'actions': [_asset_reval],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_reval('account.asset.reval')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


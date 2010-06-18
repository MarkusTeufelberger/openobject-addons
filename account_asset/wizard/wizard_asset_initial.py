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
<form string="Initial Values">
    <separator string="Initial entry" colspan="4"/>
    <label string = "Wizard for starting values of asset coming from production or investment. Use it also when you continue asset management from another system." colspan="4"/>
    <label string = "But for purchased assets use invoice line assignment." colspan="4"/>
    <field name="period_id"/>
    <field name="date"/>
    <newline/>
    <field name="name" colspan="4"/>
    <field name="acc_impairment" colspan="4"/>
    <field name="value"/>
    <field name="expense_value"/>
    <field name="intervals_before"/>
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'date': {'string': 'Date', 'type': 'date', 'required':True, 'help':"Efective date for posting."},
    'period_id': {'string': 'Period', 'type': 'many2one', 'relation':'account.period', 'required':True, 'help':"Period for posting. Consider which period to use for this posting. It should be probably some additional period before current depreciation start."},
    'name': {'string':'Description', 'type':'char', 'size':64, 'required':True},
    'value': {'string':'Base Value', 'type':'float', 'help':"Initial Base Value of method."},
    'expense_value': {'string':'Expense Value', 'type':'float', 'help':"Initial Value of method expenses. There are sum of depreciations made before this system asset management."},
    'intervals_before': {'string':'Intervals Before', 'type':'integer', 'help':"Number of intervals calculated already before asset is managed in this system."},
    'acc_impairment': {'string':'Asset Counter Account', 'type': 'many2one', 'relation':'account.account', 'required':True, 'help':"Counter account for base value."},
    'note': {'string':'Notes', 'type':'text'},
}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
#    method = method_obj.browse(cr, uid, data['id'], context)
#    asset_category_id = method.asset_id.asset_category and method.asset_id.asset_category.id or False
#    defaults = method_obj.get_defaults(cr, uid, method.method_type.id, asset_category_id, context)
#    acc_impairment = defaults and defaults.account_impairment_id and defaults.account_impairment_id.id or False
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    return {
        'note': _("Inital values for asset: "),
#        'acc_impairment': acc_impairment, 
        'date': time.strftime('%Y-%m-%d'),
        'period_id': period_id,
    }

def _asset_initial(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    method = method_obj.browse(cr, uid, data['id'], context)
    method_obj._initial(cr, uid, method, data['form']['period_id'], data['form']['date'], data['form']['value'], data['form']['expense_value'], \
            data['form']['acc_impairment'], data['form']['intervals_before'], data['form']['name'], data['form']['note'], context)
    return {}


class wizard_asset_initial(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_reval','Set Initials')
            ]}
        },
        'asset_reval': {
            'actions': [_asset_initial],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_initial('account.asset.initial')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


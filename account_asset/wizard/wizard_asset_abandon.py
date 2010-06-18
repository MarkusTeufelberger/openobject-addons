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
<form string="Abandonment">
    <separator string="Abandon Method" colspan="4"/>
    <field name="period_id"/>
    <field name="date"/>
    <newline/>
    <field name="name" colspan="4"/>
    <field name="acc_abandon" colspan = "4"/>
    <field name="whole_asset"/>
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'date': {'string': 'Date', 'type': 'date', 'required':True, 'help':"Efective date for accounting move."},
    'period_id': {'string': 'Period', 'type': 'many2one', 'relation':'account.period', 'required':True, 'help':"Calculated period and period for posting."},
    'name': {'string':'Description', 'type':'char', 'size':64, 'required':True},
    'whole_asset': {'string':'All Methods', 'type':'boolean', 'help':"Abandon all methods of this asset."},
    'acc_abandon': {'string':'Abandon Account', 'type': 'many2one', 'relation':'account.account', 'required':True, 'help':"Account for asset loss amount."},
    'note': {'string':'Notes', 'type':'text'},
}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    method = method_obj.browse(cr, uid, data['id'], context)
    asset_category_id = method.asset_id.category_id and method.asset_id.category_id.id or False
    defaults = method_obj.get_defaults(cr, uid, method.method_type.id, asset_category_id, context)
    acc_abandon = defaults and defaults.account_abandon_id and defaults.account_abandon_id.id or False
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    return {
        'note': _("Asset abandoned because: "),
        'acc_abandon': acc_abandon, 
        'date': time.strftime('%Y-%m-%d'),
        'period_id': period_id,
    }

def _asset_abandon(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    met = method_obj.browse(cr, uid, data['id'], context)
    methods = data['form']['whole_asset'] and met.asset_id.method_ids or [met]
    method_obj._abandon(cr, uid, methods, data['form']['period_id'], data['form']['date'], data['form']['acc_abandon'], \
                data['form']['name'], data['form']['note'], context)
    return {}


class wizard_asset_abandon(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_abandon','Abandon')
            ]}
        },
        'asset_abandon': {
            'actions': [_asset_abandon],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_abandon('account.asset.abandon')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


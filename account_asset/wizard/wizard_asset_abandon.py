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
from tools.translate import _

asset_end_arch = '''<?xml version="1.0"?>
<form string="Abandonment">
    <separator string="Abandon Method" colspan="4"/>
    <field name="name" colspan="4"/>
    <field name="acc_abandon" colspan = "4"/>
    <field name="whole_asset"/>
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'name': {'string':'Reason', 'type':'char', 'size':64, 'required':True},
    'whole_asset': {'string':'All Methods', 'type':'boolean', 'help':"Abandon all methods of this asset."},
    'acc_abandon': {'string':'Abandon Account', 'type': 'many2one', 'relation':'account.account', 'required':True, 'help':"Account for asset loss amount."},
    'note': {'string':'Notes', 'type':'text'},
}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    method = method_obj.browse(cr, uid, data['id'], context)
    asset_category_id = method.asset_id.asset_category and method.asset_id.asset_category.id or False
    defaults = method_obj.get_defaults(cr, uid, method.method_type.id, asset_category_id, context)
    acc_abandon = defaults and defaults.account_abandon_id and defaults.account_abandon_id.id or False
    return {
        'note': _("Asset abandoned because: "),
        'acc_abandon': acc_abandon, 
    }

def _asset_abandon(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method = pool.get('account.asset.method').browse(cr, uid, data['id'], context)
#    pool.get('account.asset.history').create(cr, uid, {
#        'type': "change",
#        'asset_method_id': data['id'],
#        'asset_id' : method.asset_id.id,
#        'name': data['form']['name'],
#        'method_delay': method.method_delay,
#        'method_period': method.method_period,
#        'note': _("Change of method parameters to:") +
#                _('\nNumber of Intervals: ')+ str(data['form']['method_delay'])+ 
#                _('\nIntervals per Year: ')+ str(data['form']['method_period'])+ 
#                _('\nProgressive Factor: ') + str(data['form']['method_progress_factor'])+
#                _('\nSalvage Value: ') + str(data['form']['method_salvage'])+ 
#                _('\nLife Quantity: ') + str(data['form']['life'])+ "\n" + str(data['form']['note']),
#    }, context)
#    pool.get('account.asset.method').write(cr, uid, [data['id']], {
#        'name': data['form']['name'],
#        'method_delay': data['form']['method_delay'],
#        'method_period': data['form']['method_period'],
#        'method_progress_factor': data['form']['method_progress_factor'],
#        'method_salvage': data['form']['method_salvage'],
#        'life': data['form']['life'],
#    }, context)
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


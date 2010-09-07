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
<form string="Method Modyfying">
    <separator string="Method parameters to modify" colspan="4"/>
    <field name="name" colspan="4"/>
    <field name="method_delay"/>
    <field name="method_period"/>
    <field name="method_progress_factor"/>
    <field name="method_salvage"/>
    <field name="life"/>
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'name': {'string':'Description', 'type':'char', 'size':64, 'required':True},
    'method_delay': {'string':'Number of Intervals', 'type':'integer'},
    'method_period': {'string':'Intervals per Year', 'type':'integer'},
    'method_progress_factor': {'string':'Progressive Factor', 'type':'float'},
    'method_salvage': {'string':'Salvage Value', 'type':'float'},
    'life': {'string':'Life Quantity', 'type':'float'},
    'note': {'string':'Notes', 'type':'text'},
}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method = pool.get('account.asset.method').browse(cr, uid, data['id'], context)
    return {
        'name': _("Modification of "),
        'method_delay': method.method_delay,
        'method_period': method.method_period,
        'method_progress_factor': method.method_progress_factor,
        'method_salvage': method.method_salvage,
        'life': method.life,

    }

def _asset_modif(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    method = method_obj.browse(cr, uid, data['id'], context)
    method_obj._modif(cr, uid, method, data['form']['method_delay'], data['form']['method_period'], data['form']['method_progress_factor'], \
                data['form']['method_salvage'], data['form']['life'], data['form']['name'], data['form']['note'], context)
    return {}

class wizard_asset_modify(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_modify','Modify Method')
            ]}
        },
        'asset_modify': {
            'actions': [_asset_modif],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_modify('account.asset.modify')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


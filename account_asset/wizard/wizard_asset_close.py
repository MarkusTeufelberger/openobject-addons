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
<form string="Method Suppression">
    <separator string="General information" colspan="4"/>
    <field name="name" colspan="4"/>
    <field name="whole_asset" colspan="4"/>    
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'name': {'string':'Description', 'type':'char', 'size':64, 'required':True},
    'whole_asset': {'string':'All Methods', 'type':'boolean'},
    'note': {'string':'Notes', 'type':'text'},

}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method = pool.get('account.asset.method').browse(cr, uid, data['id'], context)
    return {
        'note': _("Suppressed because: "),
    }


def _asset_suppress(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    met = method_obj.browse(cr, uid, data['id'], context)
    methods = data['form']['whole_asset'] and met.asset_id.method_ids or [met]
    method_obj._suppress(cr, uid, methods, data['form']['name'], data['form']['note'], context)
    return {}


class wizard_asset_close(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_suppress','Suppress Depreciation')
            ]}
        },
        'asset_suppress': {
            'actions': [_asset_suppress],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_close('account.asset.close')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


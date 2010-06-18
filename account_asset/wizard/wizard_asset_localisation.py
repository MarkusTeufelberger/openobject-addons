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
<form string="Localisation Changing">
    <separator string="Set New Localisation" colspan="4"/>
    <field name="name" colspan="4"/>
    <field name="localisation" colspan="4"/>
    <separator string="Notes" colspan="4"/>
    <field name="note" nolabel="1" colspan="4"/>
</form>'''

asset_end_fields = {
    'name': {'string':'Description', 'type':'char', 'size':64, 'required':True},
    'localisation': {'string':'Enter New localisation', 'type':'char', 'size':32, 'required':True},
    'note': {'string':'Notes', 'type':'text'},
}

def _asset_default(self, cr, uid, data, context={}):
    return {
        'note': _("Asset transfered because: "),
    }

def _asset_localisation(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    pool.get('account.asset.asset')._localisation(cr, uid, data['id'], data['form']['localisation'], data['form']['name'], data['form']['note'], context)
    return {}


class wizard_asset_localisation(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_modify','Set New Localisation')
            ]}
        },
        'asset_modify': {
            'actions': [_asset_localisation],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_localisation('account.asset.localisation')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                    Jordi Esteve <jesteve@zikzakmedia.com>
#                    Alejandro Sanchez <alejandro@asr-oss.com>
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

import wizard
import pooler
from tools.translate import _

form = """<?xml version="1.0" encoding="utf-8"?>
<form string="Bank statements import Paypal">
    <field name="file" filename="name"/>
    <newline/>
    <field name="name"/>
    <newline/>
    <field name="config_id"/>
</form>"""

fields = {
    'file': {'string': 'Bank Statements File', 'type': 'binary', 'required': True},
    'name': {'string':"File name", 'type':'char', 'size':64, 'readonly':True},
    'config_id': {'string': 'Config', 'type': 'many2one', 'relation': 'account.payment.paypal.import.config', 'required': True, },
}

result_form = """<?xml version="1.0"?>
<form string="Import Paypal Payments">
    <field name="state"/>
    <newline/>
    <separator string="Import result of Paypal payments:" colspan="6"/>
    <field name="note" colspan="6" nolabel="1"/>
</form>"""
result_fields = {
    'state': {'string':"Result", 'type':'char', 'size':64, 'readonly':True},
    'note' : {'string':'Log', 'type':'text'},
}


class import_paypal(wizard.interface):

    def _get_defaults(self, cr, uid, data, context={}):
        config_ids = pooler.get_pool(cr.dbname).get('account.payment.paypal.import.config').search(cr, uid, [])
        if len(config_ids):
            data['form']['config_id'] = config_ids[0]
        else:
            raise wizard.except_wizard(_('Warning'), _('You must define a Paypal configuration.'))
        return data['form']


    def _import(obj, cr, uid, data, context={}):
        pool = pooler.get_pool(cr.dbname)
        statement_obj = pool.get('account.bank.statement')
        (note, state) = statement_obj.paypal_import(cr, uid, data['id'], data['form']['file'], data['form']['name'], data['form']['config_id'], context=context)
        return {'note':note, 'state':state}


    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {
                'type': 'form',
                'arch': form,
                'fields': fields,
                'state': [
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('import', 'Import', 'gtk-ok', True),
                ],
            },
        },
        'import': {
            'actions': [_import],
            'result' : {'type' : 'form',
                        'arch' : result_form,
                        'fields' : result_fields,
                        'state' : [('end', 'Ok','gtk-ok') ] }
        },
    }

import_paypal('account_payment_paypal.import_paypal')

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
import mx.DateTime
from tools.translate import _

asset_end_arch = '''<?xml version="1.0"?>
<form string="Creation of Usage Lines">
    <field name="fiscal_year"/>
    <newline/>
    <field name="interval"/>
    <newline/>
    <field name="value"/>
</form>'''

asset_end_fields = {
    'fiscal_year': {'string': 'Fiscal Year', 'type': 'many2one', 'relation' : 'account.fiscalyear', 'required':True, 'help':"Choose fiscal year for entries."},
    'interval': {'string': 'Entries per Year', 'type': 'float', 'help':"How many usage entries are you going to make per year?"},
#    'name': {'string':'Description', 'type':'char', 'size':64, 'required':True},
    'value': {'string':'Entry Value', 'type':'float', 'help':"Value of Unit of Production. This value has to be changed before asset calculation but could be some indication for entering later on."},
}

def _asset_default(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    method = method_obj.browse(cr, uid, data['id'], context)
    year_obj = pool.get('account.fiscalyear')
    year = year_obj.find(cr, uid, dt = time.strftime('%Y-%m-%d'), exception = True, context=context)
#    asset_category_id = method.asset_id.asset_category and method.asset_id.asset_category.id or False
#    defaults = method_obj.get_defaults(cr, uid, method.method_type.id, asset_category_id, context)
#    acc_impairment = defaults and defaults.account_impairment_id and defaults.account_impairment_id.id or False
#    ids = pool.get('account.period').find(cr, uid, context=context)
#    period_id = False
#    if len(ids):
#        period_id = ids[0]
#    raise wizard.except_wizard(_('Error !'), _('year %s !')%year)
    return {
        'fiscal_year': year,
        'interval': method.method_period,
        'value': method.life / method.method_delay,
    }

def _asset_createlines(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    year = pool.get('account.fiscalyear').browse(cr, uid, data['form']['fiscal_year'],context)
    usage_obj = pool.get('account.asset.method.usage')
    step = 12 / data['form']['interval']
    method_id = data['id']
    for period in year.period_ids:
        if not usage_obj.search(cr, uid, [('period_id','=',period.id),('asset_method_id','=',method_id)]) and \
                ((mx.DateTime.strptime(period.date_stop, '%Y-%m-%d').month % step ) == 0):
            usage_obj.create(cr, uid, {
                'asset_method_id': method_id,
                'period_id': period.id,
                'usage': data['form']['value'],
            })
#                    and ((mx.DateTime.strptime(period.date_stop, '%Y-%m-%d').month % (12 / method.method_period)) == 0)


    return {}


class wizard_asset_usage_createlines(wizard.interface):
    states = {
        'init': {
            'actions': [_asset_default],
            'result': {'type':'form', 'arch':asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Cancel'),
                ('asset_reval','Create Lines')
            ]}
        },
        'asset_reval': {
            'actions': [_asset_createlines],
            'result': {'type' : 'state', 'state': 'end'}
        }
    }
wizard_asset_usage_createlines('account.asset.usage.createlines')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


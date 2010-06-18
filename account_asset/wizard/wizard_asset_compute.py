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
<form string="Asset Computation">
    <separator string="Generated entries" colspan="4"/>
    <field name="move_ids" readonly="1" nolabel="1"/>
</form>'''

asset_end_fields = {
    'move_ids': {'string':'Entries', 'type': 'one2many', 'relation':'account.move'},
}


asset_ask_form = '''<?xml version="1.0"?>
<form string="Asset Computation">
    <field name="period_id"/>
    <field name="date"/>
    <newline/>
    <field name="category_id"/>
    <field name="method_type_id"/>
</form>'''

asset_ask_fields = {
    'date': {'string': 'Date', 'type': 'date', 'required':True, 'help':"Efective date for accounting move."},
    'period_id': {'string': 'Period', 'type': 'many2one', 'relation':'account.period', 'required':True, 'help':"Calculated period and period for posting."},
    'category_id': {'string': 'Asset Category', 'type': 'many2one', 'relation':'account.asset.category', 'required':False, 'help': "If empty all categories assets will be calculated. If you use hierarchical categories all children of selected category be calculated."},
    'method_type_id' : {'string': 'Asset Method Type', 'type': 'many2one', 'relation':'account.asset.method.type', 'required':False, 'help': "If empty all method types will be calculated for assets."}, 
}

def _asset_compute(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    method_obj = pool.get('account.asset.method')
    period = method_obj._check_date(cr, uid, data['form']['period_id'], data['form']['date'], context)
    asset_obj = pool.get('account.asset.asset')
    if data['form']['category_id']:
        asset_ids = asset_obj.search(cr, uid, [('state','=','normal'),('category_id','child_of',[data['form']['category_id']])], context=context)
    else:
        asset_ids = asset_obj.search(cr, uid, [('state','=','normal')], context=context)
    if data['form']['method_type_id']:
        method_ids = method_obj.search(cr, uid, [('state','=','open'),('method_type','=',data['form']['method_type_id']),('asset_id','in',asset_ids)], context=context)
    else:
        method_ids = method_obj.search(cr, uid, [('state','=','open'),('asset_id','in',asset_ids)], context=context)
    ids_create = []
    for method in method_obj.browse(cr, uid, method_ids, context):
        ids_create += method_obj._compute_entries(cr, uid, method, period, data['form']['date'], context)
    self.move_ids = ids_create
    return {'move_ids': ids_create}

def _asset_open(self, cr, uid, data, context):
    value = {
        'name': _('Created moves'),
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'account.move',
        'view_id': False,
        'type': 'ir.actions.act_window'
    }
    if data['form']['move_ids']:
        value['domain']= "[('id','in',["+','.join(map(str,self.move_ids))+"])]"
    else:
        value['domain']= "[('id','=', False)]"
    return value

def _get_period(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    return {'period_id': period_id, 'date': time.strftime('%Y-%m-%d')}

class wizard_asset_compute(wizard.interface):
    states = {
        'init': {
            'actions': [_get_period],
            'result': {'type':'form', 'arch':asset_ask_form, 'fields':asset_ask_fields, 'state':[
                ('end','Cancel'),
                ('asset_compute','Compute assets')
            ]}
        },
        'asset_compute': {
            'actions': [_asset_compute],
            'result': {'type' : 'form', 'arch': asset_end_arch, 'fields':asset_end_fields, 'state':[
                ('end','Close'),
                ('asset_open','Open entries')
            ]}
        },
        'asset_open': {
            'actions': [],
            'result': {'type':'action', 'action': _asset_open,  'state':'end'}
        }
    }
wizard_asset_compute('account.asset.compute')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


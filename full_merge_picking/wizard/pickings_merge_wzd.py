# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

"""Merge pickings"""

import time

import wizard
import netsvc
import pooler
from osv.orm import browse_record, browse_null
from tools.translate import _


merge_form = """<?xml version="1.0"?>
<form string="Merge pickings">
    <separator string="Are you sure you want to merge these pickings ?"/>
    <newline/>
    <label align="0.0" string="Please note that:"/>
    <newline/>
    <label align="0.0" string="- pickings will only be merged if:"/>
    <newline/>
    <label align="0.0" string="* their status is assigned or confirmed"/>
    <newline/>
    <label align="0.0" string="* their invoice status isn't invoiced"/>
    <newline/>
    <label align="0.0" string="* are going to the same partner address"/>
    <newline/>
    <label align="0.0" string="* they belong to the same carrier"/>
    <newline/>
    <label align="0.0" string="* type is the same (in or out)"/>
</form>
"""

merge_fields = {
}

ack_form = """<?xml version="1.0"?>
<form string="Merge pickings">
    <separator string="Pickings merged"/>
</form>"""

ack_fields = {}


def _merge_orders(self, cr, uid, data, context):
    """merge pickings"""
    order_obj = pooler.get_pool(cr.dbname).get('stock.picking')

    def make_key(br, fields):
        """creates a key to group the pickings"""
        list_key = []
        for field in fields:
            field_val = getattr(br, field)
            if field in ('product_id', 'move_dest_id', 'account_analytic_id'):
                if not field_val:
                    field_val = False
            if isinstance(field_val, browse_record):
                field_val = field_val.id
            elif isinstance(field_val, browse_null):
                field_val = False
            elif isinstance(field_val, list):
                field_val = ((6, 0, tuple([v.id for v in field_val])),)
            list_key.append((field, field_val))
        list_key.sort()
        return tuple(list_key)

    # compute what the new orders should contain
    new_orders = {}

    for porder in [order for order in order_obj.browse(cr, uid, data['ids']) if order.state in ['confirmed','assigned'] and order.invoice_state != 'invoiced' and order.type in ['in','out']]:
        order_key = make_key(porder, ('address_id', 'carrier_id', 'type', 'invoice_state'))

        new_order = new_orders.setdefault(order_key, ({}, []))
        new_order[1].append(porder.id)
        order_infos = new_order[0]
        
        if not order_infos:
            order_infos.update({
                'origin': 'GROUP %s' % porder.origin,
                'invoice_state': porder.invoice_state,
                'type': porder.type,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'address_id': porder.address_id.id,
                'location_id': porder.location_id and porder.location_id.id or False,
                'auto_picking': porder.auto_picking,
                'move_type': porder.move_type,
                'note': porder.note or '',
                'state': 'draft',
                'location_dest_id': porder.location_dest_id and porder.location_dest_id.id or False,
                'carrier_id': porder.carrier_id and porder.carrier_id.id or False,
                'volume': porder.volume or 0.0,
                'weight': porder.weight or 0.0,
                'min_date': porder.min_date or False,
                'max_date': porder.max_date or False,
                'move_lines': [(6, 0, [x.id for x in porder.move_lines])],
                'sale_ids': porder.sale_id and [(6, 0, [porder.sale_id.id])] or (porder.sale_ids and [(6, 0, [x.id for x in porder.sale_ids])] or [(6, 0, [])]),
                'purchase_ids': porder.purchase_id and [(6, 0, [porder.purchase_id.id])] or (porder.purchase_ids and [(6, 0, [x.id for x in porder.purchase_ids])] or  [(6, 0, [])]),
            })
        else:
            #fields that always was updated
            if porder.note:
                order_infos['note'] = (order_infos['note'] or '') + ('\n%s' % (porder.note,))
            if porder.origin:
                order_infos['origin'] = (order_infos['origin'] or '') + ' ' + porder.origin
            if porder.volume:
                order_infos['volume'] += porder.volume
            if porder.weight:
                order_infos['weight'] += porder.weight

            if not order_infos['min_date']:
                order_infos['min_date'] = porder.min_date or False
            elif porder.min_date and porder.min_date > order_infos['min_date']:
                order_infos['min_date'] = porder.min_date or False

            if not order_infos['max_date']:
                order_infos['max_date'] = porder.max_date or False
            elif porder.max_date and porder.max_date > order_infos['max_date']:
                order_infos['max_date'] = porder.max_date or False

            if porder.move_lines:
                order_infos['move_lines'][0][2].extend([x.id for x in porder.move_lines])
            if porder.sale_id:
                order_infos['sale_ids'][0][2].append(porder.sale_id.id)
            if porder.sale_ids:
                order_infos['sale_ids'][0][2].extend([x.id for x in porder.sale_ids])
            if porder.purchase_id:
                order_infos['purchase_ids'][0][2].append(porder.purchase_id.id)
            if porder.purchase_ids:
                order_infos['purchase_ids'][0][2].extend([x.id for x in porder.purchase_ids])

    wf_service = netsvc.LocalService("workflow")

    allorders = []
    for order_key, (order_data, old_ids) in new_orders.iteritems():
        # skip merges with only one order
        if len(old_ids) < 2:
            allorders += (old_ids or [])
            continue

        # create the new order
        neworder_id = order_obj.create(cr, uid, order_data)
        allorders.append(neworder_id)
        
        # make triggers
        for old_id in order_obj.browse(cr, uid, old_ids):
            wf_service.trg_validate(uid, 'stock.picking', old_id.id, 'button_cancel', cr)

        #confirm new picking
        wf_service.trg_validate(uid, 'stock.picking', neworder_id, 'button_confirm', cr)


    if not allorders:
        raise wizard.except_wizard(_('Any valid picking for merging !'), _('Cannot find any picking valid for merging from selected items.'))

    return {
        'domain': "[('id','in', [" + ','.join(map(str, allorders)) + "])]",
        'name': _('Pickings'),
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'stock.picking',
        'view_id': False,
        'type': 'ir.actions.act_window'
    }


class merge_orders(wizard.interface):
    """Merge pickings"""
    
    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch': merge_form, 'fields' : merge_fields, 'state' : [('end', 'Cancel'), ('merge', 'Merge pickings') ]}
        },
        'merge': {
            'actions': [],
            'result': {'type': 'action', 'action': _merge_orders, 'state': 'end'}
        },
    }

merge_orders("cc.stock.picking.merge")


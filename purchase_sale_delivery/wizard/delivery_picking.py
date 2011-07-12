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

import time
import wizard
import pooler
from tools.translate import _

from tools.misc import UpdateableStr

delivery_form = UpdateableStr()

delivery_fields = {
    'carrier_id' : {'string':'Delivery Method', 'type':'many2one', 'relation': 'delivery.carrier','required':True}
}

def _delivery_default(self, cr, uid, data, context):
    order_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    order = order_obj.browse(cr, uid, data['ids'])[0]
    delivery_form.string=_("""<?xml version="1.0"?>
    <form string="Create deliveries">
        <separator colspan="4" string="Delivery Method" />
        <field name="carrier_id"/>
    </form>
    """)

    if order.state in ('done', 'cancel'):
        raise wizard.except_wizard(_('Unavailable state for picking !'), _('Picking shouldn\'t be on cancel or done state'))

    carrier_id = order.carrier_id2 and order.carrier_id2.id or False
    return {'carrier_id': carrier_id}

def _delivery_set(self, cr, uid, data, context):
    order_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    line_obj = pooler.get_pool(cr.dbname).get('stock.move')
    order_objs = order_obj.browse(cr, uid, data['ids'], context)

    for order in order_objs:
        if order.type not in ('in','out'):
            raise wizard.except_wizard(_('Unavailable type for picking !'), _('Only can add delivery lines to in or out pickings.'))

        grid_id = pooler.get_pool(cr.dbname).get('delivery.carrier').grid_get(cr, uid, [data['form']['carrier_id']], order.address_id.id)
        if not grid_id:
            raise wizard.except_wizard(_('No grid available !'), _('No grid matching for this carrier !'))
        
        grid_obj=pooler.get_pool(cr.dbname).get('delivery.grid')
        grid = grid_obj.browse(cr, uid, [grid_id])[0]

        price_unit = grid_obj.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context)

        move_id = line_obj.create(cr, uid, {
            'picking_id': order.id,
            'name': grid.carrier_id.name,
            'product_qty': 1,
            'product_uom': grid.carrier_id.product_id.uom_id.id,
            'product_id': grid.carrier_id.product_id.id,
            'price_unit': grid_obj.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context),
            'type': 'make_to_stock',
            'price_unit': price_unit,
            'shipment_line': True,
            'location_id': grid.carrier_id.product_id.property_stock_procurement.id,
            'location_dest_id': order.move_lines and order.move_lines[0].location_dest_id.id or grid.carrier_id.product_id.property_stock_inventory.id
        })

        line_obj.force_assign(cr, uid, [move_id])

        order_obj.write(cr, uid, [order.id], {'carrier_id2': data['form']['carrier_id']})


    return {}

class make_delivery(wizard.interface):
    states = {
        'init' : {
            'actions' : [_delivery_default],
            'result' : {'type' : 'form', 'arch' : delivery_form, 'fields' : delivery_fields, 'state' : [('end', 'Cancel', 'gtk-cancel'),('delivery', 'Add Delivery Costs', 'gtk-ok') ]}
        },
        'delivery' : {
            'actions' : [_delivery_set],
            'result' : {'type' : 'state', 'state' : 'end'}
        },
    }
make_delivery("cc_purchase_sale_delivery.delivery.picking")

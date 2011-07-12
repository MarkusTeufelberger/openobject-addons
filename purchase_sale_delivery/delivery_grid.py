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

"""inherit the object to avoid include shippment lines in the computation of delivery price"""

from osv import osv, fields
from tools.translate import _
from tools.safe_eval import safe_eval

class delivery_grid(osv.osv):
    """inherit the object to avoid include shippment lines in the computation of delivery price"""
    _inherit = "delivery.grid"

    def get_price_from_picking2(self, cr, uid, id, total, weight, volume, order, context={}):
        """another signature for get_price_from_picking adding gross_price computation"""
        grid = self.browse(cr, uid, id, context)

        price = 0.0
        ok = False

        for line in grid.line_ids:
            price_dict = {'price': total, 'volume':volume, 'weight': weight, 'wv':volume*weight, 'gross_price': order.price_gross}
            test = safe_eval(line.type+line.operator+str(line.max_value), price_dict)
            if test:
                if line.price_type=='variable':
                    price = line.list_price * price_dict[line.variable_factor]
                else:
                    price = line.list_price
                ok = True
                break
        if not ok:
            raise osv.except_osv(_('No price available !'), _('No line matched this order in the choosed delivery grids !'))

        return price

    def get_price(self, cr, uid, id, order, dt, context=None):
        """
        This is not very clean because the function has to check the type of order.
        It could be improve by changing the signature of the method and by passing a dict in place of a browse record.
        """
        if context is None: context = {}
        
        total = 0.0
        weight = 0.0
        volume = 0.0

        for line in order._table_name == "stock.picking" and order.move_lines or order.order_line:
            if not line.product_id or line.shipment_line:
                continue
            if line._table_name != 'purchase.order.line' and line.state == 'cancel':
                continue
            qty = 0.0

            if order._table_name == "sale.order":
                qty = line.product_uom_qty
            else:
                qty = line.product_qty

            total += line.price_subtotal or 0.0
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty

        return self.get_price_from_picking2(cr, uid, id, total, weight, volume, order, context)

delivery_grid()

class delivery_grid_line(osv.osv):
    """Adds functionality to grid lines"""

    _inherit = 'delivery.grid.line'

    _columns = {
        'type': fields.selection([('weight','Weight'),('volume','Volume'),('wv','Weight * Volume'), ('price','Price'), ('gross_price', 'Price Gross')], 'Variable', required=True),
        'variable_factor': fields.selection([('weight','Weight'),('volume','Volume'),('wv','Weight * Volume'), ('price','Price'), ('gross_price', 'Price Gross')], 'Variable Factor', required=True)
    }

delivery_grid_line()
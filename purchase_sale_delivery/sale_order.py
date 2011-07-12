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

"""Adds small functionalities for sale.order"""

from osv import osv, fields
from tools import config

class sale_order(osv.osv):
    """Adds small functionalities for sale.order"""

    _inherit = "sale.order"

    def _get_external_delivery_price(self, cr, uid, ids, name, arg, context):
        """get total of delivery lines and external delivery expenses in the invoice currency"""
        res = {}
        for sale in self.browse(cr, uid, ids):
            price = 0.0

            for dl in sale.freight_tbcollected_id:
                price += self.pool.get('res.currency').compute(cr, uid, dl.currency_id.id, sale.pricelist_id.currency_id.id, dl.price, round=True)

            res[sale.id] = price

        return res

    def _get_price_gross(self, cr, uid, ids, name, arg, context):
        """computes gross amount of sale sum(line.price_unit * line.product_qty)"""
        res = {}
        for sale in self.browse(cr, uid, ids):
            amount = 0.0
            for line in sale.order_line:
                amount += (line.price_unit * line.product_uom_qty)

            res[sale.id] = self.pool.get('res.currency').compute(cr, uid, sale.pricelist_id.currency_id.id, sale.pricelist_id.currency_id.id, amount, round=True)

        return res

    def _get_order(self, cr, uid, ids, context={}):
        """store sale order when sale.order.line changes"""
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return list(set(result.keys()))

    def _get_sale_order(self, cr, uid, ids, context={}):
        """store sale order when sale.order.line changes"""
        result = {}
        for line in self.pool.get('delivery.freight.tobe.collected').browse(cr, uid, ids, context=context):
            result[line.sale_id.id] = True
        return list(set(result.keys()))

    _columns = {
        'delivery_date': fields.date('Delivery date', help="Planned date to delivery", readonly=True, states={'draft': [('readonly', False)]}),
        'freight_tbcollected_id': fields.one2many('delivery.freight.tobe.collected', 'sale_id', 'Freight to be collected', readonly=True, states={'draft': [('readonly', False)]}),
        'end_validity_date': fields.date('End date', help="End of validity date", readonly=True, states={'draft': [('readonly', False)]}),
        'delivery_price': fields.function(_get_external_delivery_price, type="float", digits=(16, int(config['price_accuracy'])), readonly=True, method=True, string="External delivery",
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','freight_tbcollected_id'], 10),
                'sale.order.line': (_get_order, None, 10),
                'delivery.freight.tobe.collected': (_get_sale_order, None, 20)
            }),
        'price_gross': fields.function(_get_price_gross, type="float", digits=(16, int(config['price_accuracy'])), readonly=True, method=True, string="Price gross",
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'product_uom_qty'], 10),
            }),
        'incoterm_id': fields.many2one('stock.incoterms', 'Incoterms', help="International commercial terms", readonly=True, states={'draft': [('readonly', False)]}),
    }

    def action_ship_create(self, cr, uid, ids, *args):
        """extend this method to add delivery_date to picking"""
        res = super(sale_order, self).action_ship_create(cr, uid, ids, args)

        for order in self.browse(cr, uid, ids):
            pickings = [x.id for x in order.picking_ids]
            vals = {}
            if pickings:
                if  order.delivery_date:
                    vals['delivery_date'] = order.delivery_date
                if order.incoterm_id:
                    vals['incoterm_id'] = order.incoterm_id.id
                if order.carrier_id:
                    vals['carrier_id2'] = order.carrier_id.id
                if order.freight_tbcollected_id:
                    vals['freight_tbcollected_id'] = [(6, 0, [x.id for x in order.freight_tbcollected_id])]

                vals['carrier_id'] = False

                self.pool.get('stock.picking').write(cr, uid, pickings, vals)

                moves = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', pickings)])
                for move in self.pool.get('stock.move').browse(cr, uid, moves):
                    if move.sale_line_id and move.sale_line_id.shipment_line:
                        self.pool.get('stock.move').write(cr, uid, [move.id], {'shipment_line': True, 'price_unit': move.sale_line_id.price_unit})
        return res


sale_order()

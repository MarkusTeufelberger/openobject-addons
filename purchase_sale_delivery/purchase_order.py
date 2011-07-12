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

"""add some fields to object"""

from osv import osv, fields
from tools import config

class purchase_order(osv.osv):
    """add some fields to object"""

    _inherit = "purchase.order"

    def _get_external_delivery_price(self, cr, uid, ids, name, arg, context):
        """get total of delivery lines and external deliveruy expenses in the invoice currency"""
        res = {}
        for purchase in self.browse(cr, uid, ids):
            price = 0.0
            
            for dl in purchase.freight_tbcollected_id:
                price += self.pool.get('res.currency').compute(cr, uid, dl.currency_id.id, purchase.pricelist_id.currency_id.id, dl.price, round=True)

            res[purchase.id] = price

        return res

    def _get_order(self, cr, uid, ids, context={}):
        """store purchase order when purchase.order.line changes"""
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return list(set(result.keys()))

    def _get_purchase_order(self, cr, uid, ids, context={}):
        """store pucrhase order wehn purchase.order.line changes"""
        result = {}
        for line in self.pool.get('delivery.freight.tobe.collected').browse(cr, uid, ids, context=context):
            result[line.purchase_id.id] = True
        return list(set(result.keys()))

    def _get_price_gross(self, cr, uid, ids, name, arg, context):
        """computes gross amount of purchase sum(line.price_unit * line.product_qty)"""
        res = {}
        for purchase in self.browse(cr, uid, ids):
            amount = 0.0
            for line in purchase.order_line:
                amount += (line.price_base * line.product_qty)

            res[purchase.id] = self.pool.get('res.currency').compute(cr, uid, purchase.pricelist_id.currency_id.id, purchase.pricelist_id.currency_id.id, amount, round=True)

        return res

    _columns = {
        'incoterm_id': fields.many2one('stock.incoterms', 'Incoterms', help="International commercial terms", states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'date_income': fields.date('Income date', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'freight_tbcollected_id': fields.one2many('delivery.freight.tobe.collected', 'purchase_id', 'Freight to be collected', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'carrier_id':fields.many2one("delivery.carrier","Delivery method", help="Complete this field if you plan to invoice the shipping based on packings made.", states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'delivery_price': fields.function(_get_external_delivery_price, type="float", digits=(16, int(config['price_accuracy'])), readonly=True, method=True, string="External delivery",
            store={
                'purchase.order.line': (_get_order, None, 10),
                'delivery.freight.tobe.collected': (_get_purchase_order, None, 20)
            }),
        'price_gross': fields.function(_get_price_gross, type="float", digits=(16, int(config['price_accuracy'])), readonly=True, method=True, string="Price gross",
            store={
                'purchase_order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'purchase.order.line': (_get_order, ['price_base', 'product_qty'], 10),
            })
    }

    def onchange_partner_id(self, cr, uid, ids, part):
        """obtains carrier from partner"""
        result = super(purchase_order, self).onchange_partner_id(cr, uid, ids, part)
        if part:
            dtype = self.pool.get('res.partner').browse(cr, uid, part).property_delivery_carrier.id
            result['value']['carrier_id'] = dtype
        return result

    def action_picking_create(self,cr, uid, ids, *args):
        """add to new picking the incoterm_id and date_income"""
        picking_id = super(purchase_order, self).action_picking_create(cr, uid, ids, args)
        if picking_id:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id)
            self.pool.get('stock.picking').write(cr, uid, picking_id, {'incoterm_id': picking.purchase_id.incoterm_id and picking.purchase_id.incoterm_id.id or False,
                                                                        'delivery_date': picking.purchase_id.date_income,
                                                                        'carrier_id2': picking.purchase_id.carrier_id and picking.purchase_id.carrier_id.id or False,
                                                                        'freight_tbcollected_id': picking.purchase_id.freight_tbcollected_id and [(6, 0, [x.id for x in picking.purchase_id.freight_tbcollected_id])] or [(6, 0, [])],
                                                                        'carrier_id': False})

            for move in picking.move_lines:
                if move.purchase_line_id and move.purchase_line_id.shipment_line:
                    self.pool.get('stock.move').write(cr, uid, [move.id], {'shipment_line': True, 'price_unit': move.purchase_line_id.price_unit})
        return picking_id

purchase_order()
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

"""Add computed field price in stock_move with price_subtoal of his sdale_order_line or his purchase_order_line"""

from osv import osv, fields
from tools import config

class stock_move(osv.osv):
    """Add computed field price in stock_move with price_subtoal of his sdale_order_line or his purchase_order_line"""
    
    _inherit = "stock.move"

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        """get price of an purchas_line or sale_line associated to this move"""
        res = {}
        cur_obj = self.pool.get('res.currency')
        for move in self.browse(cr, uid, ids):
            res[move.id] = 0.0

            if move.sale_line_id or move.purchase_line_id:
                obj = move.sale_line_id or move.purchase_line_id
                qty = move.product_qty
                res[move.id] = obj.price_unit * qty * (1 - (obj.discount or 0.0) / 100.0)
                cur = obj.order_id.pricelist_id.currency_id
                res[move.id] = cur_obj.round(cr, uid, cur, res[move.id])

        return res

    _columns = {
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal', digits=(16, int(config['price_accuracy']))),
        'shipment_line': fields.boolean('Shipment line')
    }

    def unlink(self, cr, uid, ids, context=None):
        """allow to delete shipment lines"""
        if context is None: context = {}

        for move in self.browse(cr, uid, ids):
            if move.shipment_line:
                self.write(cr, uid,  [move.id], {'state': 'draft'})
                if move.sale_line_id:
                    self.pool.get('sale.order.line').unlink(cr, uid, [move.sale_line_id.id])
                if move.purchase_line_id:
                    self.pool.get('purchase.order.line').unlink(cr, uid, [move.purchase_line_id.id])

        return super(stock_move, self).unlink(cr, uid, ids)


stock_move()

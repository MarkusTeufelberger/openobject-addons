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

from osv import fields
from osv import osv
import time
import netsvc

import ir
from mx import DateTime
import pooler

class purchase_order_line(osv.osv):
    _name = "purchase.order.line"
    _inherit = "purchase.order.line"

    def _amount_line(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, line.price_unit * line.product_qty )
        return res

    _columns = {
        'discount': fields.float('Discount (%)', digits=(16,2), help="If you chose apply a discount for this way you will overide the option of calculate based on Price Lists, you will need to change again the product to update based on pricelists, this value must be between 0-100"),
    }
    _defaults = {
        'discount': lambda *a: 0.0,
    }
    
    def discount_change(self, cr, uid, ids, product, discount):
        if not product:
            return {'value': {'price_unit': 0.0,}}
        prod= self.pool.get('product.product').browse(cr, uid,product)
        lang=False
        res = {'value': {'price_unit': prod.standard_price*(1-discount/100),}}
        return res
purchase_order_line()

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"

    def _get_order(self, cr, uid, ids, context={}):
        """Copied from purchase/purchase.py"""
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

purchase_order()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _get_discount_invoice(self, cursor, user, move_line):
        '''Return the discount for the move line'''
        discount = 0.00
        if move_line and move_line.purchase_line_id:
            discount = move_line.purchase_line_id.discount
        return discount

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


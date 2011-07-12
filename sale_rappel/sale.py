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

"""Inherit sale_order to add rappel functionality"""

from osv import fields, osv
from tools import config

class sale_order(osv.osv):
    """Inherit sale_order to add rappel functionality"""

    _inherit ="sale.order"

    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        """calculates functions amount fields"""
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context)

        for order in self.browse(cr, uid, ids):
            if not order.rappel_percentage:
                res[order.id]['rappel_amount_untaxed'] = res[order.id]['amount_untaxed'] 
                res[order.id]['rappel_amount_tax'] = res[order.id]['amount_tax']
                res[order.id]['rappel_amount_total'] = res[order.id]['amount_total']
            else:
                res[order.id]['rappel_amount_tax'] = float(res[order.id]['amount_tax']) * (1 - (float(order.rappel_percentage) or 0.0) / 100.0)
                res[order.id]['rappel_amount_untaxed'] = float(res[order.id]['amount_untaxed']) * (1 - (float(order.rappel_percentage) or 0.0) / 100.0)
                res[order.id]['rappel_amount_total'] = float(res[order.id]['amount_total']) * (1 - (float(order.rappel_percentage) or 0.0) / 100.0)
        return res

    def _get_order(self, cr, uid, ids, context={}):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'rappel_percentage': fields.float('Rappel (%)', digits=(16, 2)),
        'rappel_amount_untaxed': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Net',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'rappel_percentage'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'rappel_amount_tax': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'rappel_percentage'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'rappel_amount_total': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'rappel_percentage'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums')
    }

sale_order()
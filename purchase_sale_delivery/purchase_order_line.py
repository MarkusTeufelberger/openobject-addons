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

class purchase_order_line(osv.osv):
    """add some fields to object"""

    _inherit = "purchase.order.line"

    _columns = {
        'shipment_line': fields.boolean('Shipment line')
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False, fiscal_position=False):
        """Heredamos el evento añadiendo algún cambio más"""
        res = super(purchase_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, date_order=date_order, fiscal_position=fiscal_position)
        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            if product_obj.description_purchase and res.get('value'):
                res['value']['notes'] = product_obj.description_purchase

        return res

purchase_order_line()
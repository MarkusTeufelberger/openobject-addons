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

"""Add new fields to stock_picking to manages purchases and sales"""

from osv import osv, fields

class stock_picking(osv.osv):
    """Add new fields to stock_picking to manages purchases and sales"""

    _inherit = 'stock.picking'

    _columns = {
        'sale_ids': fields.many2many('sale.order', 'sale_order_picking_group_rel', 'picking_id', 'sale_id', 'Sales'),
        'purchase_ids': fields.many2many('purchase.order', 'purchase_order_picking_group_rel', 'picking_id', 'purchase_id', 'Purchases')
    }

    def _invoice_hook(self, cursor, user, picking, invoice_id):
        """relates new group picking invoices to sales and to purchases"""
        res = super(stock_picking, self)._invoice_hook(cursor, user,
                picking, invoice_id)

        if not picking.sale_id and picking.sale_ids:
            self.pool.get('sale.order').write(cursor, user, [x.id for x in picking.sale_ids], {
                'invoice_ids': [(4, invoice_id)],
                })
                
        if not picking.purchase_id and picking.purchase_ids:
            self.pool.get('purchase.order').write(cursor, user, [x.id for x in picking.purchase_ids], {
                'invoice_id': invoice_id
                })
                
        return res


stock_picking()
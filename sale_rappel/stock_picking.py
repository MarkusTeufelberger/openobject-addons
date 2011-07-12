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

"""Inherit stock_picking to add rappel in create invoice from picking"""

from osv import osv

class stock_picking(osv.osv):
    
    _inherit = "stock.picking"

    def _invoice_hook(self, cr, uid, picking, invoice_id):
        '''Call after the creation of the invoice from picking, add lines for rappel if necessary'''
        #checks if rappel is define in sale order
        if picking and picking.sale_id and picking.sale_id.rappel_percentage and invoice_id:
            self.pool.get('account.invoice').write(cr, uid, invoice_id, {'rappel_discount': picking.sale_id.rappel_percentage})
            #computes rappel lines
            self.pool.get('account.invoice').compute_rappel_lines(cr, uid, invoice_id)
        return super(stock_picking, self)._invoice_hook(cr, uid, picking, invoice_id)

stock_picking()
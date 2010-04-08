# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv
from osv import fields
from tools.translate import _
from tools import config

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
    _columns = {
        'cost_price_unit': fields.float('Cost Price Unit', required=True, readonly=True, digits=(16, int(config['price_accuracy'])), help="Cost of one UoM of the product of this lot in the company's currency."),
        'uom_id': fields.many2one('product.uom', 'UoM', required=True, readonly=True, help='Unit of measure used to calculate the cost price of this lot.'),
    }
stock_production_lot()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def action_done(self, cr, uid, ids, context=None):
        result = super(stock_picking, self).action_done(cr, uid, ids, context)
        # Calculate cost price for each lot in the picking.
        for picking in self.browse(cr, uid, ids, context):
            for move in picking.move_lines:
                if not move.prodlot_id:
                    continue
                if move.prodlot_id.uom_id:
                    continue
                if move.purchase_line_id:
                    cost_price_unit = move.purchase_line_id.price_unit
                    uom_id = move.purchase_line_id.product_uom.id
                else:
                    cost_price_unit = move.product_id.standard_price
                    uom_id = move.product_id.uom_id.id
                self.pool.get('stock.production.lot').write(cr, uid, [move.prodlot_id.id], {
                    'cost_price_unit': cost_price_unit,
                    'uom_id': uom_id,
                }, context)
        return result

stock_picking()

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    def action_production_end(self, cr, uid, ids):
        result = super(mrp_production, self).action_production_end(cr, uid, ids)
        for production in self.browse(cr, uid, ids):
            cost_price = 0.0
            for move in production.move_lines:
                if not move.prodlot_id:
                    continue

                prodlot_uom_id = move.prodlot_id.uom_id.id
                qty = self.pool.get('product.uom')._compute_qty(cr, uid, move.product_uom.id, move.product_qty, prodlot_uom_id)
                cost_price += move.prodlot_id.cost_price_unit * qty

            product_id = False
            default_uom_id = False
            qty = 0.0
            lot_ids = []
            for move in production.move_created_ids:
                if not move.prodlot_id:
                    continue
                if move.prodlot_id.uom_id:
                    continue
                if product_id and product_id != move.product_id.id:
                    continue
                product_id = move.product_id.id
                default_uom_id = move.product_id.uom_id.id
                qty += self.pool.get('product.uom')._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom_id)
                lot_ids.append( move.prodlot_id.id )

            if default_uom_id and qty != 0.0:
                self.pool.get('stock.production.lot').write(cr, uid, lot_ids, {
                    'cost_price_unit': cost_price / qty,
                    'uom_id': default_uom_id,
                })

        # Calculate cost price from the cost of each lot of the products used to create this new lot.
        return result
mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

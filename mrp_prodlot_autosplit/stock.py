# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
import tools
import ir
import pooler
from tools.translate import _


class stock_move(osv.osv):
    _inherit = "stock.move"

    def copy(self, cr, uid, id, default=None, context={}):
        if not default:
            default = {}
        default['new_prodlot_code'] = False
        return super(stock_move, self).copy(cr, uid, id, default, context=context)


    def _get_prodlot_code(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for move in self.browse(cr, uid, ids):
            res[move.id] = move.prodlot_id and move.prodlot_id.name or False
        return res

    def _set_prodlot_code(self, cr, uid, ids, name, value, arg, context):
        if not value: return False

        if isinstance(ids, (int, long)):
            ids = [ids]

        for move in self.browse(cr, uid, ids):
            product_id = move.product_id.id
            existing_prodlot = move.prodlot_id
            if existing_prodlot: #avoid creating a prodlot twice
                self.pool.get('stock.production.lot').write(cr, uid, existing_prodlot.id, {'name': value})
            else:
                prodlot_id = self.pool.get('stock.production.lot').create(cr, uid, {
                    'name': value,
                    'product_id': product_id,
                })
                self.write(cr, uid, ids, {'prodlot_id': prodlot_id})


    _columns = {
        'new_prodlot_code': fields.function(_get_prodlot_code, fnct_inv=_set_prodlot_code,
                 method=True, type='char', size=64, string='Production Tracking Code To Create', select=1),
    }


#    def _check_unique_product_lot(self, cr, uid, ids):
#        for move in self.browse(cr, uid, ids):
#            if move.state == 'done' and move.product_id.unique_production_number and move.product_qty > 1 and (\
#                (move.product_id.track_production and move.location_id.usage == 'production') or \
#                (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
#                (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
#                (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer')):
#                return False
#        return True
#
#    _constraints = [
#        (_check_unique_product_lot,
#            """_(The product associated to the move require a unique (per instance) production number,
#            you should split the move assign a different number to every move)""",
#            ['prodlot_id'])]

stock_move()


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def action_assign_wkf(self, cr, uid, ids):
        result = super(stock_picking, self).action_assign_wkf(cr, uid, ids)

        for picking in self.browse(cr, uid, ids):
                additional_move_lines = []
                for move in picking.move_lines:
                    if move.product_id.unique_production_number and move.product_qty > 1 and (\
                    (move.product_id.track_production and move.location_id.usage == 'production') or \
                    (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
                    (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
                    (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer')):

                        while move.product_qty > 0:
                            new_move_id = self.pool.get('stock.move').copy(cr, uid, move.id, {'product_qty': 1, 'product_uos_qty': move.product_id.uos_coeff, 'state': move.state, 'prodlot_id': None})
                            additional_move_lines.append(new_move_id)
                            move.product_qty -= 1;

                        self.pool.get('stock.move').write(cr, uid, move.id, {'state': 'draft'})
                        self.pool.get('stock.move').unlink(cr, uid, [move.id], {})

        return result

stock_picking()


class stock_production_lot(osv.osv):
    _inherit = "stock.production.lot"

    def _last_location_id(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for prodlot_id in ids:
            cr.execute("select location_dest_id from stock_move where stock_move.prodlot_id = %s and stock_move.state='done' order by stock_move.date_planned DESC LIMIT 1" % prodlot_id)
            results = cr.fetchone()
            if results and len(results) > 0:
                res[prodlot_id] = results[0]#TODO return tuple to avoid name_get being requested by the GTK client
            else:
                res[prodlot_id] = False
        return res

    _columns = {
        'last_location_id': fields.function(_last_location_id, method=True, type="many2one", relation="stock.location", string="Last Location"),
    }

stock_production_lot()
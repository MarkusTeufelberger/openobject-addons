# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2008 Raphaël Valyi
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
from osv import fields, osv
import tools
import ir
import pooler
from tools.translate import _


class stock_move(osv.osv):
    _inherit = "stock.move"
 
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default['new_prodlot_code'] = False
        return super(stock_move, self).copy(cr, uid, id, default, context=context)


    def _get_prodlot_code(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for move in self.browse(cr, uid, ids):
            res[move.id] = move.prodlot_id and move.prodlot_id.name or False
        return res

    def _set_prodlot_code(self, cr, uid, ids, name, value, arg, context=None):
        if not value: return False

        if isinstance(ids, (int, long)):
            ids = [ids]

        for move in self.browse(cr, uid, ids, context=context):
            product_id = move.product_id.id
            existing_prodlot = move.prodlot_id
            if existing_prodlot: #avoid creating a prodlot twice
                self.pool.get('stock.production.lot').write(cr, uid, existing_prodlot.id, {'name': value})
            else:
                prodlot_id = self.pool.get('stock.production.lot').create(cr, uid, {
                    'name': value,
                    'product_id': product_id,
                })
                move.write({'prodlot_id' : prodlot_id})

    _columns = {
        'new_prodlot_code': fields.function(_get_prodlot_code, fnct_inv=_set_prodlot_code,
                                            method=True, type='char', size=64,
                                            string='Production Tracking Code To Create', select=1
                                           ),
    }

    def action_done(self, cr, uid, ids, context=None):
        """
        If we autosplit moves without reconnecting them 1 by 1, at least when some move which has descendants is split
        The following situation would happen (alphabetical order is order of creation, initially b and a pre-exists, then a is split, so a might get assigned and then split too):
        Incoming moves b, c, d
        Outgoing moves a, e, f
        Then we have those links: b->a, c->a, d->a
        and: b->, b->e, b->f
        The following code will detect this situation and reconnect properly the moves into only: b->a, c->e and d->f
        """
        result = super(stock_move, self).action_done(cr, uid, ids, context)
        for move in self.browse(cr, uid, ids):
            if move.product_id.unique_production_number and move.move_dest_id and move.move_dest_id.id:
                cr.execute("select stock_move.id from stock_move_history_ids left join stock_move on stock_move.id = stock_move_history_ids.child_id where parent_id=%s and stock_move.product_qty=1", (move.id,))
                unitary_out_moves = cr.fetchall()
                if unitary_out_moves and len(unitary_out_moves) > 1:
                    unitary_in_moves = []
                    out_node = False
                    counter = 0
                    while len(unitary_in_moves) != len(unitary_out_moves) and counter < len(unitary_out_moves):
                        out_node = unitary_out_moves[counter][0]
                        cr.execute("select stock_move.id from stock_move_history_ids left join stock_move on stock_move.id = stock_move_history_ids.parent_id where child_id=%s and stock_move.product_qty=1", (out_node,))
                        unitary_in_moves = cr.fetchall()
                        counter += 1

                    if len(unitary_in_moves) == len(unitary_out_moves):
                        unitary_out_moves.reverse()
                        unitary_out_moves.pop()
                        unitary_in_moves.reverse()
                        unitary_in_moves.pop()
                        counter = 0
                        for unitary_in_move in unitary_in_moves:
                            cr.execute("delete from stock_move_history_ids where parent_id=%s and child_id=%s", (unitary_in_moves[counter][0], out_node))
                            cr.execute("update stock_move_history_ids set parent_id=%s where parent_id=%s and child_id=%s", (unitary_in_moves[counter][0], move.id, unitary_out_moves[counter][0]))
                            counter += 1

        return result
   
    def split_move_in_single(self, cr, uid, ids, context=None):
        for move_id in ids:
            move = self.browse(cr, uid, move_id)
            qty = move.product_qty
            self.write(cr, uid, move.id, {'product_qty': 1, 'product_uos_qty': move.product_id.uos_coeff})
            while qty > 1:
                self.copy(cr, uid, move.id, {'state': move.state, 'prodlot_id': None})
                qty -= 1;
        return True

stock_move()


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def action_assign_wkf(self, cr, uid, ids):
        result = super(stock_picking, self).action_assign_wkf(cr, uid, ids)

        for picking in self.browse(cr, uid, ids):
            if self.pool.get('ir.model.fields').search(cr, uid, [('name', '=', 'company_id'), ('model', '=', 'stock.picking')]): #OpenERP v6 have the field company_id on the stock_picking but v5 doesn't have it, so we use user_id to found the company
                autosplit = picking.company_id.autosplit_is_active
            else:
                user = self.pool.get('res.users').browse(cr, uid, uid)
                autosplit = user.company_id.autosplit_is_active

            

            if autosplit:
                for move in picking.move_lines:
                    if move.product_id.unique_production_number and \
                       move.product_qty > 1 and \
                       ((move.product_id.track_production and move.location_id.usage == 'production') or \
                        (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
                        (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
                        (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer')) or True:
                            self.pool.get('stock.move').split_move_in_single(cr, uid, [move.id])

        return result

stock_picking()


class stock_production_lot(osv.osv):
    _inherit = "stock.production.lot"

    def _last_location_id(self, cr, uid, ids, field_name, arg, context={}):
        """Retrieves the last location where the product with given serial is.
        Instead of using dates we assume the product is in the location having the
        highest number of products with the given serial (should be 1 if no mistake). This
        is better than using move dates because moves can easily be encoded at with wrong dates."""
        res = {}

        for prodlot_id in ids:
            cr.execute(
                "select location_dest_id " \
                "from stock_move inner join stock_report_prodlots on stock_report_prodlots.location_id = location_dest_id and stock_report_prodlots.prodlot_id = %s " \
                "where stock_move.prodlot_id = %s and stock_move.state=%s "\
                "order by stock_report_prodlots.name DESC ",
                (prodlot_id, prodlot_id, 'done'))
            results = cr.fetchone()

            #TODO return tuple to avoid name_get being requested by the GTK client
            res[prodlot_id] = results and results[0] or False

        return res

    _columns = {
        'last_location_id': fields.function(_last_location_id, method=True,
                                            type="many2one", relation="stock.location",
                                            string="Last Location",
                                            help="The last location where the product with given serial is"),
    }

stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

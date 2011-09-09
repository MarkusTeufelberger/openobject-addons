# -*- encoding: utf-8 -*-
##############################################################################
#
#    MRP prodlot auto-split module for OpenERP
#    Copyright (C) 2008 Raphaël Valyi
#    Copyright (C) 2011 Anevia S.A. - Ability to group invoice lines
#              written by Alexis Demeaulte <alexis.demeaulte@anevia.com>
#    Copyright (C) 2011 Akretion - Ability to split lines on logistical units
#              written by Emmanuel Samyn
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
import hashlib
from tools.translate import _


class stock_move(osv.osv):
    _inherit = "stock.move"

    def copy(self, cr, uid, id, default=None, context=None):
        print "--> 1"
        if not default:
            default = {}
        default['new_prodlot_code'] = False
        return super(stock_move, self).copy(cr, uid, id, default, context=context)

    def _get_prodlot_code(self, cr, uid, ids, field_name, arg, context=None):
        print "--> 2"
        res = {}
        for move in self.browse(cr, uid, ids):
            res[move.id] = move.prodlot_id and move.prodlot_id.name or False
        return res

    def _set_prodlot_code(self, cr, uid, ids, name, value, arg, context=None):
        print "--> 3"
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

    def _get_tracking_code(self, cr, uid, ids, field_name, arg, context=None):
        print "--> 2"
        res = {}
        for move in self.browse(cr, uid, ids):
            res[move.id] = move.tracking_id and move.tracking_id.name or False
        return res

    def _set_tracking_code(self, cr, uid, ids, name, value, arg, context=None):
        print "--> 3"
        if not value: return False

        if isinstance(ids, (int, long)):
            ids = [ids]

        for move in self.browse(cr, uid, ids, context=context):
            product_id = move.product_id.id
            existing_tracking = move.tracking_id
            if existing_tracking: #avoid creating a tracking twice
                self.pool.get('stock.tracking').write(cr, uid, existing_tracking.id, {'name': value})
            else:
                tracking_id = self.pool.get('stock.tracking').create(cr, uid, {
                    'name': value,
                })
                move.write({'tracking_id' : tracking_id})

    _columns = {
        'new_prodlot_code': fields.function(_get_prodlot_code, fnct_inv=_set_prodlot_code,
                                            method=True, type='char', size=64,
                                            string='Prodlot fast input', select=1
                                           ),
        'new_tracking_code': fields.function(_get_tracking_code, fnct_inv=_set_tracking_code,
                                            method=True, type='char', size=64,
                                            string='Tracking fast input', select=1
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
        print "--> 4"
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
        print "--> 5.1"
        all_ids = ids[:]
        for move_id in ids:
            move = self.browse(cr, uid, move_id)
            qty = move.product_qty
            self.write(cr, uid, move.id, {'product_qty': 1, 'product_uos_qty': move.product_id.uos_coeff})
            while qty > 1:
                all_ids.append( self.copy(cr, uid, move.id, {'state': move.state, 'prodlot_id': None}) )
                qty -= 1;
        return all_ids

	# To split move lines depending on logistical units defined for the product
	# TO IMPROVE with 1 (or more) algo which will take into account all LU for the product
    def split_move_in_lu(self, cr, uid, ids, context=None):
        print "--> 5.2"
        all_ids = ids[:]
        for move_id in ids:
            move = self.browse(cr, uid, move_id)
            qty = move.product_qty
            lu_qty = move.product_id.packaging[0].qty
            # Set existing move to LU quantity
            self.write(cr, uid, move.id, {'product_qty': lu_qty, 'product_uos_qty': move.product_id.uos_coeff})
            qty -= lu_qty
            # While still enough qty to create a new move, create it
            while qty >= lu_qty:
                all_ids.append( self.copy(cr, uid, move.id, {'state': move.state, 'prodlot_id': None}) )
                qty -= lu_qty;
            # Create a last move for the remainder qty
            all_ids.append( self.copy(cr, uid, move.id, {'state': move.state, 'prodlot_id': None, 'product_qty':qty}) )            
        return all_ids
        
stock_move()


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def action_assign_wkf(self, cr, uid, ids):
        print "--> 6"
        result = super(stock_picking, self).action_assign_wkf(cr, uid, ids)

        for picking in self.browse(cr, uid, ids):
            if picking.company_id.autosplit_is_active:
                for move in picking.move_lines:
                    # SPLIT in single line
                    if move.product_id.lot_split_type=="single" and \
                       move.product_qty > 1 and \
                       ((move.product_id.track_production and move.location_id.usage == 'production') or \
                        (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
                        (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
                        (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer')):
                            self.pool.get('stock.move').split_move_in_single(cr, uid, [move.id])
                            print "--> 6.1" 
                    # SPLIT with logistical units
                    elif move.product_id.lot_split_type=="lu" and \
                       move.product_qty > 1 and move.product_id.packaging and \
                       ((move.product_id.track_production and move.location_id.usage == 'production') or \
                        (move.product_id.track_production and move.location_dest_id.usage == 'production') or \
                        (move.product_id.track_incoming and move.location_id.usage == 'supplier') or \
                        (move.product_id.track_outgoing and move.location_dest_id.usage == 'customer')):
                            self.pool.get('stock.move').split_move_in_lu(cr, uid, [move.id])
                            print "--> 6.2"                       

        return result

    # Because stock move line can be splitted by the module, we merge
    # invoice lines (if option 'is_group_invoice_line' is activated for the company)
    # at the following conditions :
    #   - the product is the same and
    #   - the discount is the same and
    #   - the unit price is the same and
    #   - the description is the same and
    #   - taxes are the same
    #   - they are from the same sale order lines (requires extra-code)
    # we merge invoice line together and do the sum of quantity and
    # subtotal.
    def action_invoice_create(self, cursor, user, ids, journal_id=False,
        group=False, type='out_invoice', context=None):
        print "--> 7"
        invoice_dict = super(stock_picking, self).action_invoice_create(cursor, user,
            ids, journal_id, group, type, context=context)

        for picking_key in invoice_dict:
            invoice = self.pool.get('account.invoice').browse(cursor, user, invoice_dict[picking_key], context=context)
            if not invoice.company_id.is_group_invoice_line:
                continue

            new_line_list = {}

            for line in invoice.invoice_line:

                # Build a key
                key = unicode(line.product_id.id) + ";" \
                    + unicode(line.discount) + ";" \
                    + unicode(line.price_unit) + ";" \
                    + line.name + ";"

                # Add the tax key part
                tax_tab = []
                for tax in line.invoice_line_tax_id:
                    tax_tab.append(tax.id)
                tax_tab.sort()
                for tax in tax_tab:
                    key = key + unicode(tax) + ";"

                # Add the sale order line part but check if the field exist because
                # it's install by a specific no-trunk-community-addons
                if self.pool.get('ir.model.fields').search(cursor, user, [('name', '=', 
                        'sale_order_lines'), ('model', '=', 'account.invoice.line')], context=context) != []:
                    order_line_tab = []
                    for order_line in line.sale_order_lines:
                        order_line_tab.append(order_line.id)
                    order_line_tab.sort()
                    for order_line in order_line_tab:
                        key = key + unicode(order_line) + ";"


                # Get the hash of the key
                hash_key = hashlib.sha224(key.encode('utf8')).hexdigest()

                # Check if the key already exist
                if not new_line_list.has_key(hash_key):
                    new_line_list[hash_key] = {
                        'id': line.id,
                        'quantity': line.quantity,
                        'price_subtotal': line.price_subtotal,
                    }

                else:
                    new_line_list[hash_key]['quantity'] = new_line_list[hash_key]['quantity'] + line.quantity
                    new_line_list[hash_key]['price_subtotal'] = new_line_list[hash_key]['price_subtotal'] \
                                                            +  line.price_subtotal
                    self.pool.get('account.invoice.line').unlink(cursor, user, line.id, context=context)

            # Write modifications made on invoice lines
            for hash_key in new_line_list:
                line_id = new_line_list[hash_key]['id']
                del new_line_list[hash_key]['id']
                self.pool.get('account.invoice.line').write(cursor, user, line_id, new_line_list[hash_key], context=context)

        return invoice_dict

stock_picking()


class stock_production_lot(osv.osv):
    _inherit = "stock.production.lot"

    def _last_location_id(self, cr, uid, ids, field_name, arg, context={}):
        """Retrieves the last location where the product with given serial is.
        Instead of using dates we assume the product is in the location having the
        highest number of products with the given serial (should be 1 if no mistake). This
        is better than using move dates because moves can easily be encoded at with wrong dates."""
        print "--> 8"
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
                                            string="Last location",
                                            help="Display the current stock location of this production lot"),
    }

stock_production_lot()


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

"""Add new relationship with stock_picking on purchases"""

from osv import osv, fields
import netsvc
from tools.translate import _

class purchase_order(osv.osv):
    """Add new relationship with stock_picking on purchases"""

    _inherit = "purchase.order"

    def _shipped_rate(self, cr, uid, ids, name, arg, context=None):
        """compute the shipped rate from picking moves"""
        if not ids: return {}
        res = {}
        for order in self.browse(cr, uid, ids):
            res[order.id] = [0.0,0.0]

        cr.execute('''SELECT
                p.id,sum(m.product_qty), m.state
            FROM
                stock_move m
            INNER JOIN
                purchase_order_line pl on (pl.id=m.purchase_line_id)
            INNER JOIN
                purchase_order p on (p.id=pl.order_id)
            WHERE
                p.id in %s
            GROUP BY m.state, p.id''',
                   (tuple(ids),))

        for oid,nbr,state in cr.fetchall():
            if state=='cancel':
                continue
            if state=='done':
                res[oid][0] += nbr or 0.0
                res[oid][1] += nbr or 0.0
            else:
                res[oid][1] += nbr or 0.0
        for r in res:
            if not res[r][1]:
                res[r] = 0.0
            else:
                res[r] = 100.0 * res[r][0] / res[r][1]
        return res

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            tot = 0.0
            tot_pamount = 0.0
            if purchase.invoice_id and purchase.invoice_id.state not in ('draft','cancel'):
                tot += purchase.invoice_id.amount_untaxed

            purchase_ids = self.search(cursor, user, [('invoice_id', '=', purchase.invoice_id.id),('state', '!=', 'cancel')])
            for pur in self.browse(cursor, user, purchase_ids):
                tot_pamount += pur.amount_untaxed

            if purchase.amount_untaxed and tot:
                result = tot * 100.0 / tot_pamount
                res[purchase.id] = result > 100 and 100.0 or result
            else:
                res[purchase.id] = 0.0
        return res


    _columns = {
        'group_picking_ids': fields.many2many('stock.picking', 'purchase_order_picking_group_rel', 'purchase_id', 'picking_id', 'Picking group'),
        'shipped_rate': fields.function(_shipped_rate, method=True, string='Received', type='float'),
        'invoiced_rate': fields.function(_invoiced_rate, method=True, string='Invoiced', type='float')
    }


    def action_merge_picking_assign(self, cr, uid, ids, *args):
        """assigns the group picking to active picking"""
        picking_id = False

        for order in self.browse(cr, uid, ids):
            if order.group_picking_ids:
                for pick in order.group_picking_ids:
                    if pick.state != 'cancel':
                        picking_id = pick.id

        return picking_id

    def check_can_cancel(self, cr, uid, ids, *args):
        """Checks if was created new group picking or relly the first group picking was cancelled"""
        for order in self.browse(cr, uid, ids):
            if order.group_picking_ids:
                for pick in order.group_picking_ids:
                    if pick.state != 'cancel':
                        return True

        return False
    
    def action_cancel(self, cr, uid, ids, context={}):
        """cancel lines on group picking if exists"""
        if context is None: context = {}
        res = super(purchase_order, self).action_cancel(cr, uid, ids, context=context)

        pickings = []

        for order in self.browse(cr, uid, ids):
            if order.group_picking_ids:
                for line in order.order_line:
                    moves = self.pool.get('stock.move').search(cr, uid, [('purchase_line_id', '=', line.id)])
                    for move in self.pool.get('stock.move').browse(cr, uid, moves):
                        if move.picking_id and move.picking_id.state in ('draft','cancel'):
                            pickings.append(move.picking_id.id)
                        elif move.picking_id:
                            raise osv.except_osv(
                                _('Could not cancel purchase order !'),
                                _('You must first cancel all packing attached to this purchase order.'))
                    if moves:
                        self.pool.get('stock.move').action_cancel(cr, uid, moves)

        if pickings:
            pickings = list(set(pickings))

            for picking in self.pool.get('stock.picking').browse(cr, uid, pickings):
                cancel = True
                for move in picking.move_lines:
                    if move.state != 'cancel':
                        cancel = False
                        break

                if cancel:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_cancel', cr)

        return res
    
purchase_order()
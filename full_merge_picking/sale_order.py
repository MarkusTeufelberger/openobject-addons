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

"""Add new relationship with stock_picking on sales"""

from osv import osv, fields
import netsvc
from tools.translate import _

class sale_order(osv.osv):
    """Add new relationship with stock_picking on sales"""

    _inherit = "sale.order"

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        """rate to 0.0 if sale is cancelled"""
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                res[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    tot += invoice.amount_untaxed

            if tot and sale.state != 'cancel':
                res[sale.id] = min(100.0, tot * 100.0 / (sale.amount_untaxed or 1.00))
            else:
                res[sale.id] = 0.0
        return res

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        """not invoiced if is cancelled"""
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = True
            for invoice in sale.invoice_ids:
                if invoice.state != 'paid' or sale.state == 'cancel':
                    res[sale.id] = False
                    break
            if not sale.invoice_ids:
                res[sale.id] = False
        return res

    def _invoiced_search(self, cursor, user, obj, name, args, context):
        """copy of original method because I will want to overwrite the field"""
        if not len(args):
            return []
        clause = ''
        no_invoiced = False
        for arg in args:
            if arg[1] == '=':
                if arg[2]:
                    clause += 'AND inv.state = \'paid\''
                else:
                    clause += 'AND inv.state <> \'paid\''
                    no_invoiced = True
        cursor.execute('SELECT rel.order_id ' \
                'FROM sale_order_invoice_rel AS rel, account_invoice AS inv ' \
                'WHERE rel.invoice_id = inv.id ' + clause)
        res = cursor.fetchall()
        if no_invoiced:
            cursor.execute('SELECT sale.id ' \
                    'FROM sale_order AS sale ' \
                    'WHERE sale.id NOT IN ' \
                        '(SELECT rel.order_id ' \
                        'FROM sale_order_invoice_rel AS rel)')
            res.extend(cursor.fetchall())
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    _columns = {
        'group_picking_ids': fields.many2many('stock.picking', 'sale_order_picking_group_rel', 'sale_id', 'picking_id', 'Picking group'),
        'invoiced_rate': fields.function(_invoiced_rate, method=True, string='Invoiced', type='float'),
        'invoiced': fields.function(_invoiced, method=True, string='Paid',
            fnct_search=_invoiced_search, type='boolean')
    }


    def action_cancel(self, cr, uid, ids, context={}):
        """cancel lines on group picking if exists"""
        if context is None: context = {}
        res = super(sale_order, self).action_cancel(cr, uid, ids, context=context)

        pickings = []

        for order in self.browse(cr, uid, ids):
            if order.group_picking_ids:
                for line in order.order_line:
                    moves = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', '=', line.id), ('state', '!=', 'cancel')])
                    for move in self.pool.get('stock.move').browse(cr, uid, moves):
                        if move.picking_id and move.picking_id.state in ('draft', 'cancel'):
                            pickings.append(move.picking_id.id)
                        elif move.picking_id:

                            raise osv.except_osv(
                                _('Could not cancel sale order !'),
                                _('You must first cancel all packing attached to this sale order.'))
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

sale_order()
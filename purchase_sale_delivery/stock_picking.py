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

"""adds incoterm field to pickings"""

from osv import fields, osv
from tools import config

class stock_picking(osv.osv):
    """adds incoterm field to pickings"""
    _inherit = "stock.picking"

    def _get_external_del_was_invoiced(self, cr, uid, ids, name, arg, context):
        """returns if the external_delivery_lines_was_invoiced"""
        res = {}
        for picking in self.browse(cr, uid, ids):
            res[picking.id] = True
            for dline in picking.freight_tbcollected_id:
                if dline.invoice_id and dline.invoice_id.state != 'cancel':
                    continue
                res[picking.id] = False
                break
        return res

    def _get_price_gross(self, cr, uid, ids, name, arg, context):
        """computes gross amount of picking sum(move.price_unit * move.product_qty)"""
        res = {}
        for pick in self.browse(cr, uid, ids):
            amount = 0.0
            for move in pick.move_lines:
                amount += (move.price_unit or (move.sale_line_id and move.sale_line_id.price_unit or (move.purchase_line_id and move.purchase_line_id.price_base or 0.0)) * move.product_qty)

            currency = pick.sale_id and pick.sale_id.pricelist_id.currency_id.id or (pick.purchase_id and pick.purchase_id.pricelist_id.currency_id.id or False)
            if not currency:
                currency = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id


            res[pick.id] = self.pool.get('res.currency').compute(cr, uid, currency, currency, amount, round=True)

        return res

    def _get_picking(self, cr, uid, ids, context={}):
        """store stock picking when move lines changed"""
        result = {}
        for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if move.picking_id:
                result[move.picking_id.id] = True
            else:
                continue
        return list(set(result.keys()))

    def _search_external_dels_was_invoices(self, cr, uid, obj, name, args, context):
        """allow search to this field"""
        if not len(args):
            return []
        ids = []
        for dline in self.pool.get('delivery.freight.tobe.collected').browse(cr, uid, self.pool.get('delivery.freight.tobe.collected').search(cr, uid, [])):
            if args[0][1] == '=' and args[0][2] == True and dline.invoice_id and dline.invoice_id.state != 'cancel':
                ids.append(dline.id)
            elif args[0][1] == '=' and args[0][2] == False and (not dline.invoice_id or dline.invoice_id.state == 'cancel'):
                ids.append(dline.id)
            elif (args[0][1] == '!=' or args[0][1] == '<>') and args[0][2] == True and (not dline.invoice_id or dline.invoice_id.state == 'cancel'):
                ids.append(dline.id)
            elif (args[0][1] == '!=' or args[0][1] == '<>') and args[0][2] == False and dline.invoice_id and dline.invoice_id.state != 'cancel':
                ids.append(dline.id)

        return [('id', 'in', list(set([x.picking_id.id for x in self.pool.get('delivery.freight.tobe.collected').browse(cr, uid, ids)])))]

    _columns = {
        'incoterm_id': fields.many2one('stock.incoterms', 'Incoterms', readonly=True, help="International commercial terms"),
        'delivery_date': fields.date('Delivery date', help="Planned date to delivery"),
        'external_delivery_invoiced': fields.function(_get_external_del_was_invoiced, fnct_search=_search_external_dels_was_invoices, type="boolean", method=True, string='External deliveries invoiced'),
        'freight_tbcollected_id': fields.one2many('delivery.freight.tobe.collected', 'picking_id', 'Freight to be collected'),
        'carrier_id2':fields.many2one("delivery.carrier", "Carrier"),
        'price_gross': fields.function(_get_price_gross, type="float", digits=(16, int(config['price_accuracy'])), readonly=True, method=True, string="Price gross",
            store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['sale_id', 'purchase_id', 'move_lines'], 10),
                'stock.move': (_get_picking, ['price_unit', 'product_qty', 'sale_line_id', 'purchase_line_id'], 10),
            }),
    }

    def _get_price_unit_invoice(self, cursor, user, move_line, type):
        '''Return the price unit for the move line'''
        if move_line.shipment_line:
            return move_line.price_unit
        else:
            return super(stock_picking, self)._get_price_unit_invoice(cursor, user, move_line, type)


stock_picking()

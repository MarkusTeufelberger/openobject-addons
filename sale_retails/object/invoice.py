# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_retails module for OpenERP, allows the management of deposit
#
#    Copyright (C) 2009 Smile.fr. All Rights Reserved
#    authors: Raphaël Valyi
#
#    Copyright (C) 2010 SYLEAM Info Services (<http://www.syleam.fr/>) Suzanne Jean-Sebastien
#
#    This file is a part of sale_retails
#
#    sale_retails is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_retails is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields
from osv import osv
import netsvc
from sets import Set


class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    _columns = {
        'sale_order_ids': fields.many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Orders'),
    }
    
    def action_move_create(self, cr, uid, ids, *args):
        """Reconciling back deposits payments at invoice validation. Will only work if payments moves are validated before."""
        res = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
        
        for invoice in self.browse(cr, uid, ids):
            if invoice.sale_order_ids:
                all_sale_related_invoices = Set([])
                for sale_order in invoice.sale_order_ids:
                    for sale_order_line in sale_order.order_line:
                        for invoice_line in sale_order_line.invoice_lines:
                            all_sale_related_invoices.add(invoice_line.invoice_id)

                all_sale_related_invoices_move_lines = []
                for invoice in all_sale_related_invoices:
                    for move_id in self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', invoice.move_id.id)]):
                            move_line = self.pool.get('account.move.line').browse(cr, uid, move_id)
                            if move_line.account_id == invoice.partner_id.property_account_receivable:
                                all_sale_related_invoices_move_lines.append(move_line.id)
                                break
                
                counter_parts = []
                for sale_order in invoice.sale_order_ids:
                    for payment in sale_order.payment_ids:
                        if sale_order.shop_id.deposit_validation == "invoice_confirm":
                            self.pool.get('account.move').post(cr, uid, [payment.move_id.id], *args)
                        if not payment.reconcile_id:
                            counter_parts.append(self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', payment.move_id.id), ('sale_id', '=', False)])[0])
                try:
	                self.pool.get('account.move.line').reconcile_partial(cr, uid, counter_parts + all_sale_related_invoices_move_lines, 'manual', *args)
                except Exception:
                    pass
        return res

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
#
##############################################################################

from tools import config
from osv import fields, osv

from decimal import Decimal
from math import ceil, floor


class Invoice(osv.osv):
    """Add rounding utilities."""
    _inherit = 'account.invoice'

    # We have to redefine function because it does not call button_reset_taxes
    # don't ask me why...
    def action_move_create(self, cursor, uid, ids, *args):
        for inv in self.browse(cursor, uid, ids):
            if not inv.tax_line:
                self.button_reset_taxes(cursor, uid, [inv.id], context=None)
        res = super(Invoice, self).action_move_create(cursor, uid, ids, *args)
        return res

    def button_reset_taxes(self, cursor, uid, ids, context=None):
        """Override invoice function to compute rounding."""
        res = super(Invoice, self).button_reset_taxes(cursor, uid, ids, context)
        if not context:
            context = {}
        user = self.pool.get('res.users').browse(cursor, uid, uid)
        company = user.company_id
        ait_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        factor = int(100 / company.rounding)
        for inv_id in ids:
            invoice = self.browse(cursor, uid, inv_id)
            if invoice.type not in ('out_invoice', 'out_refund'):
                continue
            to_del = inv_line_obj.search(
                        cursor,
                        uid,
                        [('invoice_id', '=', invoice.id), ('rounding_line', '=', True)]
            )
            if to_del:
                inv_line_obj.unlink(cursor, uid, to_del)
                invoice = self.browse(cursor, uid, inv_id)
            if company.rounding_policy == 'even':
                rounded_amount = round(invoice.amount_total * factor) / factor
            elif company.rounding_policy == 'up':
                rounded_amount = ceil(invoice.amount_total * factor) / factor
            elif company.rounding_policy == 'down':
                rounded_amount = floor(invoice.amount_total * factor) / factor
            qtz = Decimal('.' + '0' * int(config['price_accuracy']))
            round_correction = float(Decimal(str(rounded_amount)).quantize(qtz) -
                                     Decimal(str(invoice.amount_total)).quantize(qtz))
            if round_correction:
                lang = invoice.partner_id.lang
                label = self.pool.get('res.company').browse(cursor, uid, company.id, {'lang': lang}).rounding_name
                if company.rounding_in_line:
                    inv_line_obj.create(cursor, uid, {
                        'invoice_id': invoice.id,
                        'name': label,
                        'price_unit': round_correction,
                        'account_id': company.rounding_account.id,
                        'qty': 1,
                        'rounding_line': True,
                    })
                else:
                    ait_obj.create(cursor, uid, {
                        'invoice_id': invoice.id,
                        'name': label,
                        'amount': round_correction,
                        'account_id': company.rounding_account.id,
                    })
        return res

Invoice()


class InvoiceLine(osv.osv):
    """Flag for rounding lines."""
    _inherit = 'account.invoice.line'
    _columns = {
        'rounding_line': fields.boolean('Rounding line')
    }

InvoiceLine()

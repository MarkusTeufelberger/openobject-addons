# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    amazonerpconnect for OpenERP                                               #
#    Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>   #
#                                                                               #
#    This program is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU Affero General Public License as             #
#    published by the Free Software Foundation, either version 3 of the         #
#    License, or (at your option) any later version.                            #
#                                                                               #
#    This program is distributed in the hope that it will be useful,            #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#    GNU Affero General Public License for more details.                        #
#                                                                               #
#    You should have received a copy of the GNU Affero General Public License   #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                               #
#################################################################################

from osv import osv, fields


class account_tax_code(osv.osv):
    _inherit='account.tax'
    
    def get_tax_from_rate(self, cr, uid, rate, is_tax_included=False, context=None):
        #TODO improve, if tax are not correctly mapped the order should be in exception (integration with sale_execption)
        tax_ids = self.pool.get('account.tax').search(cr, uid, [('price_include', '=', is_tax_included),
                ('type_tax_use', '=', 'sale'), ('amount', '>=', rate - 0.001), ('amount', '<=', rate + 0.001)])
        if tax_ids and len(tax_ids) > 0:
            return tax_ids[0]
        else:
        #try to find a tax with less precision 
            tax_ids = self.pool.get('account.tax').search(cr, uid, [('price_include', '=', is_tax_included), 
                    ('type_tax_use', '=', 'sale'), ('amount', '>=', rate - 0.01), ('amount', '<=', rate + 0.01)])
            if tax_ids and len(tax_ids) > 0:
                return tax_ids[0]
        return False

account_tax_code()


class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def auto_reconcile_single(self, cr, uid, invoice_id, context=None):
        obj_move_line = self.pool.get('account.move.line')
        invoice = self.browse(cr, uid, invoice_id, context=context)
        line_ids = obj_move_line.search(
            cr, uid,
            ['|', '|',
                ('ref', '=', invoice.origin),
                # keep ST_ for backward compatibility
                # previously the voucher ref
                ('ref', '=', "ST_%s" % invoice.origin),
                ('ref', '=', invoice.move_id.ref),
             ('reconcile_id', '=', False),
             ('account_id', '=', invoice.account_id.id)],
            context=context)
        lines = obj_move_line.read(
            cr, uid, line_ids, ['debit', 'credit'], context=context)
        if lines:
            # handle also the case of the invoice with a amount at 0.0
            # when we have 1 move line (no payment)
            # or eventually 2 payments for one invoice
            sums = reduce(
                lambda line, memo:
                    dict((key, value + memo[key])
                    for key, value
                    in line.iteritems()
                    if key in ('debit', 'credit')), lines)
            balance = sums['debit'] - sums['credit']
            precision = self.pool.get('decimal.precision').precision_get(
                cr, uid, 'Account')
            if not round(balance, precision):
                obj_move_line.reconcile(cr, uid, line_ids, context=context)
                return True

        return False

    def auto_reconcile(self, cr, uid, ids, context=None):
        for invoice_id in ids:
            self.auto_reconcile_single(cr, uid, invoice_id, context=context)
        return True

account_invoice()

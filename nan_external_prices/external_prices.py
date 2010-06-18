##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L.  All Rights Reserved.
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

import time
from osv import osv, fields
from tools import config

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _original_amount_all(self, cr, uid, ids, field_name, arg, context):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        result = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context)
        for order in self.browse(cr, uid, ids, context):
            if order.use_external_prices:
                amount_tax = 0.0
                amount_untaxed = 0.0
                for line in order.order_line:
                    amount_tax += line.external_tax_amount
                    amount_untaxed += line.external_base_amount

                result[order.id]['amount_tax'] = amount_tax
                result[order.id]['amount_untaxed'] = amount_untaxed
                result[order.id]['amount_total'] = amount_untaxed + amount_tax
        return result

    def _get_order(self, cr, uid, ids, context={}):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        # Inherited fields
        'amount_untaxed': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','use_external_prices'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums'),
        'amount_tax': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','use_external_prices'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums'),
        'amount_total': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line','use_external_prices'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums'),
        # Added fields
        'use_external_prices': fields.boolean('Use External Prices', help='Use prices imported from external system or online shop.'),
    }

    def _inv_get(self, cr, uid, order, context={}):
        result = super(sale_order, self)._inv_get(cr, uid, order, context)
        result['use_external_prices'] = order.use_external_prices
        return result

sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        result = super(sale_order_line, self)._amount_line(cr, uid, ids, field_name, arg, context)
        for line in self.browse(cr, uid, ids, context):
            if line.order_id.use_external_prices:
                result[line.id] = line.external_base_amount
        return result

    _columns = {
        # Inherited field
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal', digits=(16, int(config['price_accuracy']))),
        # Added fields
        'external_tax_amount': fields.float('External Tax Invoiced', digits=(16, int(config['price_accuracy'])), readonly=True, help='Tax Amount in external system or online shop if the order was imported.'),
        'external_base_amount': fields.float('External Base Raw Total', digits=(16, int(config['price_accuracy'])), readonly=True, help='Base amount in external system or online shop if the order was imported.'),

        'external_tax_percent': fields.float('External Tax Percent', digits=(16, int(config['price_accuracy'])), readonly=True, help='Tax Percentage Applied in Magento.'),
        'external_base_original_price': fields.float('External Original Base Price', digits=(16, int(config['price_accuracy'])), readonly=True, help='Original Base Price in Magento.'),
        'external_base_tax_amount': fields.float('External Base Tax Amount', digits=(16, int(config['price_accuracy'])), readonly=True, help='Base Tax Amount in Magento.'),
    }

    def invoice_line_create(self, cr, uid, ids, context={}):
        result = super(sale_order_line, self).invoice_line_create(cr, uid, ids, context)
        for line in self.browse(cr, uid, ids, context):
            # Note: We only support the case when the *order line* is invoiced *all at once*.
            # Cases in which the same order line has several invoice lines will not work properly.
            for invoice_line in line.invoice_lines:
                self.pool.get('account.invoice.line').write(cr, uid, invoice_line.id, {
                    'external_tax_amount': line.external_tax_amount,
                    'external_base_amount': line.external_base_amount,
                }, context)
        return result

sale_order_line()


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'use_external_prices': fields.boolean('Use External Pricing', help='Use prices imported from external system or online shop.'),
    }


account_invoice()

class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'

    def compute(self, cr, uid, invoice_id, context={}):
        tax_grouped = super(account_invoice_tax, self).compute(cr, uid, invoice_id, context)
        invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context)
        if invoice.use_external_prices:
            company_currency = invoice.company_id.currency_id.id
            if len(tax_grouped) > 1:
                raise osv.except_osv(_('Error'), _('There should be only one tax line when external prices are used.'))
            for tax in tax_grouped.values():
                tax_amount = 0.0
                base_amount = 0.0
                for line in invoice.invoice_line:
                    tax_amount += line.external_tax_amount
                    base_amount += line.external_base_amount
                tax['base'] = base_amount
                tax['amount'] = tax_amount
                tax['base_amount'] = self.pool.get('res.currency').compute(cr, uid, invoice.currency_id.id, company_currency, tax['base'], context={'date': invoice.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                tax['tax_amount'] = self.pool.get('res.currency').compute(cr, uid, invoice.currency_id.id, company_currency, tax['amount'], context={'date': invoice.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
        return tax_grouped

account_invoice_tax()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        result = super(account_invoice_line, self)._amount_line(cr, uid, ids, field_name, arg, context)
        for line in self.browse(cr, uid, ids, context):
            if line.invoice_id.use_external_prices:
                result[line.id] = line.external_base_amount
        return result

    def _amount_line2(self, cr, uid, ids, field_name, arg, context):
        result = super(account_invoice_line, self)._amount_line2(cr, uid, ids, field_name, arg, context)
        for line in self.browse(cr, uid, ids, context):
            if line.invoice_id.use_external_prices:
                result[line.id]['price_subtotal_incl'] = line.external_base_amount + line.external_tax_amount
        return result

    def _get_invoice(self, cr, uid, ids, context):
        result = {}
        for inv in self.pool.get('account.invoice').browse(cr, uid, ids, context=context):
            for line in inv.invoice_line:
                result[line.id] = True
        return result.keys()

    _columns = {
        # Inherited field
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal',store=True, type="float", digits=(16, int(config['price_accuracy']))),

        # Inherited field from module account_tax_include
        'price_subtotal_incl': fields.function(_amount_line2, method=True, string='Subtotal', multi='amount', store={
            'account.invoice': (_get_invoice,['price_type'],10), 
            'account.invoice.line': (lambda self,cr,uid,ids,c={}: ids,None,10)
        }),

        # Added fields
        'external_tax_amount': fields.float('External Tax Invoiced', digits=(16, int(config['price_accuracy'])), readonly=True, help='Tax Amount in external system or online shop if the invoice or the corresponding order was imported.'),
        'external_base_amount': fields.float('External Base Raw Total', digits=(16, int(config['price_accuracy'])), readonly=True, help='Base amount in external system or online shop if the invoice or the corresponding order was imported.'),
    }
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

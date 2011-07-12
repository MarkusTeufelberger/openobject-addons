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

"""Inherit account_invoice to racalculate from button the rappel in invoices"""

from osv import osv, fields
from tools.translate import _

class account_invoice(osv.osv):
    """Inherit account_invoice to recompute from button the rappel in invoices"""

    _inherit = 'account.invoice'

    _columns = {
        'rappel_discount': fields.float('Rappel (%)', digits=(16, 2))
    }

    _defaults = {
        'rappel_discount': lambda *a: 0.0
    }

    def calculate_rappel_price_unit(self, cr, uid, invoice_line_ids, rappel_percentage):
        """calculates rappel price_unit"""
        total_net_price = 0.0
        for invoice_line in self.pool.get('account.invoice.line').browse(cr, uid, invoice_line_ids):
            total_net_price += invoice_line.price_subtotal
        return float(total_net_price) - (float(total_net_price) * (1 - (float(rappel_percentage) or 0.0) / 100.0))

    def compute_rappel_lines(self, cr, uid, id):
        """creates rappel lines"""
        invoice = self.browse(cr, uid, id)
        rappels = {}
        inv_lines_out_vat = []
        for invoice_line in invoice.invoice_line:
            if invoice_line.invoice_line_tax_id:
                for tax in invoice_line.invoice_line_tax_id:
                    if tax.tax_group == 'vat' and str(tax.id) not in rappels:
                        rappels[str(tax.id)] = [invoice_line.id]
                    elif tax.tax_group == 'vat' and str(tax.id) in rappels:
                        rappels[str(tax.id)].append(invoice_line.id)
                #check if invoice_line is in dictionary or not
                y = []
                for x in rappels.values():
                    y.extend(x)
                if invoice_line.id not in list(set(y)):
                    inv_lines_out_vat.append(invoice_line.id)
            else:
                #lines without defined vat
                inv_lines_out_vat.append(invoice_line.id)
        prod_rappel_id = self.pool.get('product.product').search(cr, uid, [('name', '=', 'Rappel'), ('default_code', '=', '999')])[0]
        prod_rappel = self.pool.get('product.product').browse(cr, uid, prod_rappel_id)
        for rappel_line in rappels:
            self.pool.get('account.invoice.line').create(cr, uid, {
                    'name': (len(rappels) > 1 and _("Rappel discount, (%s)") % self.pool.get('account.tax').browse(cr, uid, int(rappel_line)).name or _("Rappel discount")) + " " + str(invoice.rappel_discount) + "%",
                    'invoice_id': id,
                    'product_id': prod_rappel.id,
                    'account_id': prod_rappel.categ_id.property_account_income_categ.id,
                    'price_unit': 0.0 - (self.calculate_rappel_price_unit(cr, uid, rappels[rappel_line], invoice.rappel_discount)),
                    'quantity': 1,
                    'invoice_line_tax_id': [(6, 0, [int(rappel_line)])]
                    })
        if inv_lines_out_vat:
            self.pool.get('account.invoice.line').create(cr, uid, {
                    'name': _("Rappel discount") + " " + str(invoice.rappel_discount) + "%",
                    'invoice_id': id,
                    'product_id': prod_rappel.id,
                    'account_id': prod_rappel.categ_id.property_account_income_categ.id,
                    'price_unit': 0.0 - (self.calculate_rappel_price_unit(cr, uid, inv_lines_out_vat, invoice.rappel_discount)),
                    'quantity': 1
                    })

        #recalculates taxes
        self.button_compute(cr, uid, [id], set_total=(type in ('in_invoice', 'in_refund')))

        return True

    def button_reset_rappel(self, cr, uid, ids, context=None):
        """recomputes rappel in invoice"""
        if context == None: context = {}
        for invoice in self.browse(cr, uid, ids):
            if invoice.rappel_discount:
                #create list with all rappel lines to delete, new rappel lines will be created
                orig_rappel_lines = []
                #searches for rappel product
                product_ids = self.pool.get('product.product').search(cr, uid, [('name', '=', 'Rappel'), ('default_code', '=', '999')])
                rappel_prod = self.pool.get('product.product').browse(cr, uid, product_ids[0])
                for invoice_line in invoice.invoice_line:
                    if invoice_line.product_id.id == rappel_prod.id:
                        orig_rappel_lines.append(invoice_line.id)

                if orig_rappel_lines:
                    #delete old rappel lines
                    self.pool.get('account.invoice.line').unlink(cr, uid, orig_rappel_lines)

                self.compute_rappel_lines(cr, uid, invoice.id)
        return True

account_invoice()
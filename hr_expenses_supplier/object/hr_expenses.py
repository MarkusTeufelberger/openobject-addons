# -*- coding: utf-8 -*-
##############################################################################
#
#    hr_expenses_supplier module for OpenERP, add supplier in expenses lines
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
#
#    This file is a part of hr_expenses_supplier
#
#    hr_expenses_supplier is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    hr_expenses_supplier is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _

class hr_expense_expense(osv.osv):
    _inherit = 'hr.expense.expense'

    def action_invoice_create(self, cr, uid, ids):
        res = False
        invoice_obj = self.pool.get('account.invoice')
        for exp in self.browse(cr, uid, ids):
            lines = []
            line_expenses = {}
            if not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error !'), _('The employee must have a contact home address'))
            for l in exp.line_ids:
                tax_id = []
                if l.product_id:
                    acc = l.product_id.product_tmpl_id.property_account_expense.id
                    if not acc:
                        acc = l.product_id.categ_id.property_account_expense_categ.id
                    tax_id = [x.id for x in l.product_id.supplier_taxes_id]
                else:
                    acc = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category')
                    if not acc:
                        raise osv.except_osv(_('Error !'), _('Please configure Default Expanse account for Product purchase, `property_account_expense_categ`'))
                line_expenses = {
                    'name': l.name,
                    'account_id': acc,
                    'price_unit': l.unit_amount,
                    'quantity': l.unit_quantity,
                    'uos_id': l.uom_id.id,
                    'product_id': l.product_id and l.product_id.id or False,
                    'invoice_line_tax_id': tax_id and [(6, 0, tax_id)] or False,
                    'account_analytic_id': l.analytic_account.id,
                }

                if l.partner_id:
                    acc = l.partner_id.property_account_payable.id
                    payment_term_id = l.partner_id.property_payment_term.id
                    inv = {
                        'name': exp.name,
                        'reference': self.pool.get('ir.sequence').get(cr, uid, 'hr.expense.invoice'),
                        'account_id': acc,
                        'type': 'in_invoice',
                        'partner_id': l.partner_id.id,
                        'address_invoice_id': l.partner_id.address_get( ['invoice'])['invoice'],
                        'address_contact_id': l.partner_id.address_get( ['contact'])['contact'],
                        'origin': exp.name,
                        'invoice_line': [(0, False, line_expenses)],
                        'price_type': 'tax_included',
                        'currency_id': exp.currency_id.id,
                        'payment_term': payment_term_id,
                        'fiscal_position': l.partner_id.property_account_position.id
                    }
                    if payment_term_id:
                        to_update = invoice_obj.onchange_payment_term_date_invoice(cr, uid, [],
                                payment_term_id, None)
                        if to_update:
                            inv.update(to_update['value'])
                    if exp.journal_id:
                        inv['journal_id']=exp.journal_id.id
                    inv_id = invoice_obj.create(cr, uid, inv, {'type':'in_invoice'})
                    invoice_obj.button_compute(cr, uid, [inv_id], {'type':'in_invoice'},
                            set_total=True)
                    self.write(cr, uid, [exp.id], {'invoice_id': inv_id, 'state': 'invoiced'})
                else:
                    lines.append((0, False, line_expenses))

            acc = exp.employee_id.address_home_id.partner_id.property_account_payable.id
            payment_term_id = exp.employee_id.address_home_id.partner_id.property_payment_term.id
            inv = {
                'name': exp.name,
                'reference': self.pool.get('ir.sequence').get(cr, uid, 'hr.expense.invoice'),
                'account_id': acc,
                'type': 'in_invoice',
                'partner_id': exp.employee_id.address_home_id.partner_id.id,
                'address_invoice_id': exp.employee_id.address_home_id.id,
                'address_contact_id': exp.employee_id.address_home_id.id,
                'origin': exp.name,
                'invoice_line': lines,
                'price_type': 'tax_included',
                'currency_id': exp.currency_id.id,
                'payment_term': payment_term_id,
                'fiscal_position': exp.employee_id.address_home_id.partner_id.property_account_position.id
            }
            if payment_term_id:
                to_update = invoice_obj.onchange_payment_term_date_invoice(cr, uid, [],
                        payment_term_id, None)
                if to_update:
                    inv.update(to_update['value'])
            if exp.journal_id:
                inv['journal_id']=exp.journal_id.id
            inv_id = invoice_obj.create(cr, uid, inv, {'type':'in_invoice'})
            invoice_obj.button_compute(cr, uid, [inv_id], {'type':'in_invoice'},
                    set_total=True)
            self.write(cr, uid, [exp.id], {'invoice_id': inv_id, 'state': 'invoiced'})
            res = inv_id
        return res
hr_expense_expense()

class hr_expense_line(osv.osv):
    _inherit = 'hr.expense.line'

    _columns = {
        'partner_id':fields.many2one('res.partner', "Supplier", change_default=True),
    }
hr_expense_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


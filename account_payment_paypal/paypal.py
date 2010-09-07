# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#                       Alejandro Sanchez <alejandro@asr-oss.com>
#    $Id$
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

from osv import osv,fields
import tools
from tools.translate import _
import os
import base64
import time
import datetime
import netsvc
import csv

class Log(Exception):
    def __init__(self):
        self.content = ""
        self.error = False
    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error
    def __call__(self):
        return self.content
    def __str__(self):
        return self.content


class account_payment_paypal_import_config(osv.osv):
    _name = 'account.payment.paypal.import.config'
    _description = 'Paypal payments Configuration'

    _columns = {
        'name' : fields.char('Name',size=40),
        'active': fields.boolean('Active'),
        'activate_insert': fields.boolean('Active Insert', help="Check this box if you want to insert the Paypal transactions in the bank statement. If not, it only shows the warning or error messages."),
        'account_expenditure_id': fields.many2one('account.account', 'Payment fee account', required=True, help="Account for the Paypal fees."),
        'status_completed': fields.boolean('Status completed', help="Check this box if you want to process only the Paypal transactions with the status field = 'Completed'."),
        'invoice_reconcile': fields.boolean('Search invoice to reconcile', help="Check this box when, if an invoice to reconcile have not found by the Paypal transaction ID, you want to find an open invoice with same partner, same amount+-accuracy, same date+-accuracy and payment type 'PAYPAL'."),
        'invoice_amount_accuracy': fields.float('Invoice amount accuracy (%)', help="Payment amount accuracy (% ratio between 0-1) on searching an invoice to reconcile."),
        'invoice_date_accuracy': fields.integer('Invoice date accuracy', help="Payment date accuracy (number of days) on searching an invoice to reconcile."),
    }

    _defaults = {
        'active': lambda *a: 1,
        'activate_insert': lambda *a: 0,
        'invoice_amount_accuracy': lambda *a: 0.01,
        'invoice_date_accuracy': lambda *a: 1,
    }
account_payment_paypal_import_config()


class account_bank_statement(osv.osv):
    _inherit = "account.bank.statement"


    def paypal_search_customer_invoice(self, cr, uid, row, config, context=None):
        """If you want to search the customer invoice using other filters,
           you can redefine this method in your own module"""
        if context == None:
            context = {}
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, [
            ('state','=','open'),
            ('type','=','out_invoice'),
            ('name', 'like', '%'+row['Transaction ID']+'%')
        ], context=context)
        return invoice_ids


    def paypal_search_supplier_invoice(self, cr, uid, row, config, context=None):
        """If you want to search the supplier invoice using other filters,
           you can redefine this method in your own module"""
        if context == None:
            context = {}
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, [
            ('state','=','open'),
            ('type','=','in_invoice'),
            ('reference', '=', row['Reference Txn ID'][3:])
        ], context=context)
        return invoice_ids


    def paypal_payment_line_fields(self, row):
        """If you want compute additional fields or update them in paypal payment lines,
           you can redefine this method in your own module"""
        vals = {
            #'field_name': row['field_name']
        }
        return vals


    def paypal_fee_line_fields(self, row):
        """If you want compute additional fields or update them in paypal fee lines,
           you can redefine this method in your own module"""
        vals = {
            #'field_name': row['field_name']
        }
        return vals


    def paypal_extra_info(self, cr, uid, row, config, context=None):
        """If you want create additonal information in OpenERP objects related to paypal payment,
           you can redefine this method in your own module"""
        if context == None:
            context = {}
        return True


    def paypal_import(self, cr, uid, id, file, filename, config_id, context=None):
        statement_line_obj = self.pool.get('account.bank.statement.line')
        move_line_obj = self.pool.get('account.move.line')
        partner_obj = self.pool.get('res.partner')
        property_obj = self.pool.get('ir.property')
        attachment_obj = self.pool.get('ir.attachment')
        invoice_obj = self.pool.get('account.invoice')
        move_line_obj = self.pool.get('account.move.line')
        bank_obj = self.pool.get('res.bank')
        partner_bank_obj = self.pool.get('res.partner.bank')
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        config_obj = self.pool.get('account.payment.paypal.import.config')
        cur_obj = self.pool.get('res.currency')

        if context == None:
            context = {}
        config = config_obj.browse(cr, uid, config_id)
        company_currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id

        log = Log()
        warnings = ''
        file2 = base64.decodestring(file)
        st = self.browse(cr, uid, id)

        if st.state == 'confirm':
            log.add(_('Wrong import\n\nSummary:\n '), True)
            log.add(_('The bank statement is alredy confirmed. It can not be imported from file.'), True)
            return (log(), _('Error'))

        try:
            unicode(file2, 'utf8')
        except Exception, e: # If we can not convert to UTF-8 maybe the file is codified in ISO-8859-1: We convert it.
            file2 = unicode(file2, 'iso-8859-1').encode('utf-8')
            #print e
            #raise wizard.except_wizard(_('Error !'), _('File to import codified in ISO-8859-1')

        file2 = file2.split('\n')
        file2[0] = file2[0].replace(', ',',')
        reader = csv.DictReader(file2, delimiter=',', quotechar='"')

        bank_ids = bank_obj.search(cr, uid, [('name', '=', 'PAYPAL')])
        bank_id = bank_ids and bank_ids[0] or False
        if not bank_id:
            log.add(_('Wrong import\n\nSummary:\n '), True)
            log.add(_('Bank type PAYPAL not found'), True)
            return (log(), _('Error'))

        invoice_list = []
        credit_payment = 0.0
        debit_payment = 0.0
        balance_payment = 0.0
        count = count_noupdate = 0
        account_receivable = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)
        account_payable = property_obj.get(cr, uid, 'property_account_payable', 'res.partner', context=context)

        for row in reader:
            # Filter status
            if config.status_completed and row['Status'] != 'Completed':
                continue
            # Filter currency: Don't add Paypal lines with a different currency of the bank statement one
            if row['Currency'] != st.currency.name:
                continue

            partner_id = False
            account_id = account_receivable
            invoice = False
            date_transaction = datetime.datetime.strptime(row['Date'],"%d/%m/%Y").strftime("%Y-%m-%d")
            ref_payment = row['Transaction ID']
            amount_payment = (row['Gross'] != '' and float(row['Gross'].replace(".","").replace(",","."))) or 0.0
            if row['Type'] in ['Web Accept Payment Received', 'Payment Received', 'Subscription Payment Received', 'Refund']:
                type_payment = 'customer'
                debit_payment -= amount_payment
            elif row['Type'] in ['Credit']:
                type_payment = 'supplier'
                credit_payment += amount_payment
            else: # ['Transfer', 'Chargeback Settlement']
                type_payment = 'general'
                credit_payment += amount_payment
                name_payment = row['Type']

            # Filter repeated Paypal lines (check Paypal Transaction ID stored in ref)
            cr.execute("SELECT l.id FROM account_bank_statement_line l JOIN account_bank_statement s ON l.statement_id=s.id WHERE l.ref like '%s' AND s.journal_id=%s" % ('%'+ref_payment+'%',st.journal_id.id,))
            if cr.fetchone() != None:
                warnings += _("\nWARNING: Paypal payment with Transaction ID %s is repeated,") % (ref_payment)
                count_noupdate += 1
                continue

            if type_payment == 'customer':
                # Search invoice by name (ref payment)
                name_payment = row['From Email Address']
                invoice_ids = self.paypal_search_customer_invoice(cr, uid, row, config, context)
                invoice_ids = [x for x in invoice_ids if x not in invoice_list]
                invoice_id = invoice_ids and invoice_ids[0] or False
                if invoice_id:
                    invoice = invoice_obj.browse(cr, uid, invoice_id)
                    account_id = invoice.account_id.id
                    partner_id = invoice.partner_id.id
                else:
                    account_id = account_receivable
                    warnings += _("\nWARNING: Invoice with Transaction ID %s not found,") % (ref_payment)
                    #count_noupdate += 1
                    #continue

            elif type_payment == 'supplier':
                name_payment = row['To Email Address']
                invoice_ids = self.paypal_search_supplier_invoice(cr, uid, row, config, context)
                invoice_ids = [x for x in invoice_ids if x not in invoice_list]
                invoice_id = invoice_ids and invoice_ids[0] or False
                if invoice_id:
                    invoice = invoice_obj.browse(cr, uid, invoice_id)
                    account_id = invoice.account_id.id
                    partner_id = invoice.partner_id.id
                else:
                    account_id = account_payable
                    warnings += _("\nWARNING: Invoice with Transaction ID %s not found,") % (ref_payment)
                    #count_noupdate += 1
                    #continue

            # If any partner has not found from invoice, try to find it from his paypal name account
            if not partner_id and type_payment != 'general':
                partner_bank_ids = partner_bank_obj.search(cr, uid, [('acc_number', '=', name_payment),('bank', '=',  bank_id)])
                if partner_bank_ids:
                    partner_banks = partner_bank_obj.browse(cr, uid, partner_bank_ids)
                    partner_ids = [x.partner_id.id for x in partner_banks]
                    partner = partner_banks[0].partner_id
                    partner_id = partner.id
                    account_id = type_payment == 'customer' and partner.property_account_receivable.id or partner.property_account_payable.id

            # Search invoice
            if not invoice and partner_id and config.invoice_reconcile:
                invoice_amount = amount_payment > 0 and amount_payment or -amount_payment
                date_pay = datetime.date(int(date_transaction[:4]), int(date_transaction[5:7]), int(date_transaction[8:]))
                date_accuracy = datetime.timedelta(days=config.invoice_date_accuracy)
                first = date_pay - date_accuracy
                last  = date_pay + date_accuracy
                d_first = "%04i-%02i-%02i" % (first.year, first.month, first.day)
                d_last  = "%04i-%02i-%02i" % (last.year, last.month, last.day)

                invoice_ids = invoice_obj.search(cr, uid,
                    [('state','=','open'),
                    ('payment_type', '=', 'PAYPAL'),
                    ('amount_total', '>=', invoice_amount*(1-config.invoice_amount_accuracy)),
                    ('amount_total', '<=', invoice_amount*(1+config.invoice_amount_accuracy)),
                    ('date_invoice', '>=', d_first),
                    ('date_invoice', '<=', d_last),
                    ('currency_id', '=', st.currency.id),
                    ('partner_id', 'in', partner_ids)],
                    order='date_invoice')
                invoice_ids = [x for x in invoice_ids if x not in invoice_list]
                invoice_id = invoice_ids and invoice_ids[0] or False

                # If not found, try to find an invoice with the company currency if it is different from statement currency
                if not invoice_id and company_currency_id != st.currency.id:
                    invoice_amount = cur_obj.compute(cr, uid, st.currency.id, company_currency_id, invoice_amount, context={'date': date_transaction})
                    invoice_ids = invoice_obj.search(cr, uid,
                        [('state','=','open'),
                        ('payment_type', '=', 'PAYPAL'),
                        ('amount_total', '>=', invoice_amount*(1-config.invoice_amount_accuracy)),
                        ('amount_total', '<=', invoice_amount*(1+config.invoice_amount_accuracy)),
                        ('date_invoice', '>=', d_first),
                        ('date_invoice', '<=', d_last),
                        ('currency_id', '=', company_currency_id),
                        ('partner_id', 'in', partner_ids)],
                        order='date_invoice')
                    invoice_ids = [x for x in invoice_ids if x not in invoice_list]
                    invoice_id = invoice_ids and invoice_ids[0] or False
                if invoice_id:
                    invoice = invoice_obj.browse(cr, uid, invoice_id)
                    partner_id = invoice.partner_id.id
                    account_id = invoice.account_id.id
                    if invoice.amount_total - invoice_amount:
                        warnings += _("\nWARNING: Invoice %s and its payment have a difference %f,") % (invoice.number, invoice.amount_total - invoice_amount)

            # Reconcile payment line with invoice (move lines)
            reconcile_id = False
            if invoice and invoice.move_id:
                invoice_list.append(invoice_id)
                cr.execute("select id from account_move_line l where account_id in (select id from account_account where type in ('payable', 'receivable') and active) and reconcile_id is null and move_id=%s" % invoice.move_id.id)
                res = cr.fetchall()
                if len(res):
                    if config.activate_insert:
                        reconcile_id = statement_reconcile_obj.create(cr, uid, {
                            'line_ids': [(6, 0, map(lambda x:x[0], res))]
                            }, context=context)

            values = {
                'name': name_payment,
                'date': date_transaction,
                'amount': amount_payment,
                'ref': ref_payment,
                'type': type_payment,
                'statement_id': id,
                'account_id': account_id,
                'partner_id': partner_id,
                'reconcile_id': reconcile_id,
                'note': row['Reference Txn ID'] and 'Reference Txn '+row['Reference Txn ID']+'\n' or '' + row.get('Address Line 1','')+row.get('Address Line 2/District','')+'\n'+row.get('Town/City','')+' '+row.get('State/Province/Region/County/Territory/Prefecture/Republic','')+'\n'+row.get('Zip/Postal Code','')+' '+row.get('Country','')+'\n'+row.get('Contact Phone Number',''),
            }
            values.update(self.paypal_payment_line_fields(row)) # Adds additional fields or updates fields
            #print values
            if config.activate_insert:
                statement_line_obj.create(cr, uid, values, context=context)

            # Paypal fees
            expenditure_payment = (row['Fee'] != '' and float(row['Fee'].replace(".","").replace(",","."))) or 0.0
            if expenditure_payment != 0.0:
                credit_payment += expenditure_payment
                values = {
                    'name': _('PayPal fee'),
                    'date': date_transaction,
                    'amount': expenditure_payment,
                    'ref': ref_payment,
                    'type': 'general',
                    'statement_id': id,
                    'account_id': config.account_expenditure_id.id,
                    'partner_id': partner_id,
                }
                values.update(self.paypal_fee_line_fields(row)) # Adds additional fields or updates fields
                #print values
                if config.activate_insert:
                    statement_line_obj.create(cr, uid, values, context=context)

            self.paypal_extra_info(cr, uid, row, config, context=context)
            count += 1

        balance_payment = st.balance_start + credit_payment - debit_payment
        if config.activate_insert:
            self.write(cr, uid, id, {'balance_end_real': balance_payment}, context=context)
            attachment_obj.create(cr, uid, {
                'name': filename,
                'datas': file,
                'datas_fname': filename,
                'res_model': 'account.bank.statement',
                'res_id': id,
                }, context=context)
            cr.commit() # Must do a commit to import very big files
            log.add(_("Successful import.\n\nSummary:\n Total added payments: %d\n") % (count))
        else:
            log.add(_("Active Insert disabled, nothing has been added/updated.\n\nSummary:\n Total added payments: %d\n") % (count))

        if count_noupdate != 0:
            log.add(_(" Total not added payments: %d\n") % (count_noupdate))
        log.add(warnings)
        return (log(), _('Success'))

account_bank_statement()



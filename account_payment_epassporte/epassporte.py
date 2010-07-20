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
import os
from tools.translate import _
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


class account_payment_epassporte_import_config(osv.osv):
    _name = 'account.payment.epassporte.import.config'
    _description = 'Epassporte payments Configuration'

    _columns = {
        'name' : fields.char('Name',size=40),
        'active': fields.boolean('Active'),
        'activate_insert' : fields.boolean('Active Insert', help="Check this box if you want to insert the ePassporte transactions in the bank statement. If not, it only shows the warning or error messages."),
        'account_expenditure_id': fields.many2one('account.account', 'Payment fee account', required=True, help="Account for the ePassporte fees."),
        'invoice_reconcile': fields.boolean('Search invoice to reconcile', help="Check this box when you want to find an open invoice to reconcile with same partner, same amount+-accuracy, same date+-accuracy and payment type 'EPASSPORTE'."),
        'invoice_amount_accuracy': fields.float('Invoice amount accuracy (%)', help="Payment amount accuracy (% ratio between 0-1) on searching an invoice to reconcile."),
        'invoice_date_accuracy': fields.integer('Invoice date accuracy', help="Payment date accuracy (number of days) on searching an invoice to reconcile."),
    }

    _defaults = {
        'active': lambda *a: 1,
        'activate_insert': lambda *a: 0,
        'invoice_amount_accuracy': lambda *a: 0.01,
        'invoice_date_accuracy': lambda *a: 1,
    }
account_payment_epassporte_import_config()


class account_bank_statement(osv.osv):
    _inherit = "account.bank.statement"

    def epassporte_payment_line_fields(self, row):
        """If you want compute additional fields or update them in epassporte payment lines,
           you can redefine this method in your own module"""
        vals = {
            #'field_name': row['field_name']
        }
        return vals


    def epassporte_fee_line_fields(self, row):
        """If you want compute additional fields or update them in epassporte fee lines,
           you can redefine this method in your own module"""
        vals = {
            #'field_name': row['field_name']
        }
        return vals


    def epassporte_extra_info(self, cr, uid, row, config, context=None):
        """If you want create additonal information in OpenERP objects related to epassporte payment,
           you can redefine this method in your own module"""
        if context == None:
            context = {}
        return True


    def epassporte_import(self, cr, uid, id, file, filename, config_id, context=None):
        statement_line_obj = self.pool.get('account.bank.statement.line')
        move_line_obj = self.pool.get('account.move.line')
        partner_obj = self.pool.get('res.partner')
        property_obj = self.pool.get('ir.property')
        model_fields_obj = self.pool.get('ir.model.fields')
        attachment_obj = self.pool.get('ir.attachment')
        invoice_obj = self.pool.get('account.invoice')
        move_line_obj = self.pool.get('account.move.line')
        bank_obj = self.pool.get('res.bank')
        partner_bank_obj = self.pool.get('res.partner.bank')
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        config_obj = self.pool.get('account.payment.epassporte.import.config')
        property_obj = self.pool.get('ir.property')
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
        reader = csv.DictReader(file2, delimiter=',', quotechar='"')

        bank_ids = bank_obj.search(cr, uid, [('name', '=', 'EPASSPORTE')])
        bank_id = bank_ids and bank_ids[0] or False
        if not bank_id:
            log.add(_('Wrong import\n\nSummary:\n '), True)
            log.add(_('Bank type EPASSPORTE not found'), True)
            return (log(), _('Error'))

        invoice_list = []
        credit_payment = 0.0
        debit_payment = 0.0
        balance_payment = 0.0
        count = count_noupdate = 0
        ref_payment = None
        partner_id = None
        account_receivable = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)
        account_payable = property_obj.get(cr, uid, 'property_account_payable', 'res.partner', context=context)

        # ePassporte file is ordered from new to old date
        for row in reversed(list(reader)):
            # Check if Bank statement currency and ePassporte file currency match
            if 'Amount in '+st.currency.name not in row:
                log.add(_('Wrong import\n\nSummary:\n '), True)
                log.add(_('Bank statement currency and ePassporte file currency are different.'), True)
                return (log(), _('Error'))

            amount_payment = float(row['Amount in '+st.currency.name])
            date_transaction = datetime.datetime.strptime(row['Transaction Date'],"%m/%d/%Y").strftime("%Y-%m-%d")
            if row['Description'][:7] not in ['b2p Fee', 'b2b Fee']:
                ref_payment = row['Description']

            if row['Description'][:7] in ['b2p Fee', 'b2b Fee']:
                credit_payment += amount_payment
                values = {
                    'name': _('ePassporte fee'),
                    'date': date_transaction,
                    'amount': amount_payment,
                    'ref': ref_payment,
                    'type': 'general',
                    'statement_id': id,
                    'account_id': config.account_expenditure_id.id,
                    'partner_id': partner_id,
                }
                values.update(self.epassporte_fee_line_fields(row)) # Adds additional fields or updates fields
                if config.activate_insert:
                    statement_line_obj.create(cr, uid, values, context=context)
                continue

            # Filter repeated ePassporte lines (check the same DESCRIPTION + AMOUNT + DATE)
            cr.execute("SELECT l.id FROM account_bank_statement_line l JOIN account_bank_statement s ON l.statement_id=s.id WHERE l.ref = '%s' AND l.amount = '%s' AND l.date = '%s' AND s.journal_id=%s" % (ref_payment, amount_payment, date_transaction, st.journal_id.id,))
            if cr.fetchone() != None:
                warnings += _("\nWARNING: ePassporte payment with Transaction ID %s is repeated (Amount: %s, Date: %s),") % (ref_payment, amount_payment, date_transaction)
                count_noupdate += 1
                continue

            if amount_payment > 0:
                type_payment = 'customer'
            else:
                type_payment = 'supplier'

            # Search partner id by partner_bank
            if row['Description'][:3] in ['b2p','b2b'] and row['Description'][4:7] != 'Fee':
                partner_bank_name = name_payment = row['Description'][4:]
            elif row['Description'][:5] == 'Load:':
                partner_bank_name = name_payment = row['Description'][6:]
            else:
                partner_bank_name = name_payment = row['Description']

            partner_bank_ids = partner_bank_obj.search(cr, uid, [('acc_number', '=', partner_bank_name),('bank', '=',  bank_id)])
            if partner_bank_ids:
                partner_banks = partner_bank_obj.browse(cr, uid, partner_bank_ids)
                partner_ids = [x.partner_id.id for x in partner_banks]
                partner = partner_banks[0].partner_id
                partner_id = partner.id
                account_id = type_payment == 'customer' and partner.property_account_receivable.id or partner.property_account_payable.id

                # Search invoice
                invoice_id = False
                if config.invoice_reconcile:
                    invoice_amount = amount_payment > 0 and amount_payment or -amount_payment
                    date_pay = datetime.date(int(date_transaction[:4]), int(date_transaction[5:7]), int(date_transaction[8:]))
                    date_accuracy = datetime.timedelta(days=config.invoice_date_accuracy)
                    first = date_pay - date_accuracy
                    last  = date_pay + date_accuracy
                    d_first = "%04i-%02i-%02i" % (first.year, first.month, first.day)
                    d_last  = "%04i-%02i-%02i" % (last.year, last.month, last.day)

                    invoice_ids = invoice_obj.search(cr, uid,
                        [('state', '=', 'open'),
                        ('payment_type', '=', 'EPASSPORTE'),
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
                            [('state', '=', 'open'),
                            ('payment_type', '=', 'EPASSPORTE'),
                            ('amount_total', '>=', invoice_amount*(1-config.invoice_amount_accuracy)),
                            ('amount_total', '<=', invoice_amount*(1+config.invoice_amount_accuracy)),
                            ('date_invoice', '>=', d_first),
                            ('date_invoice', '<=', d_last),
                            ('currency_id', '=', company_currency_id),
                            ('partner_id', 'in', partner_ids)],
                            order='date_invoice')
                        invoice_ids = [x for x in invoice_ids if x not in invoice_list]
                        invoice_id = invoice_ids and invoice_ids[0] or False

                # Reconcile payment line with invoice (move lines)
                reconcile_id = False
                if invoice_id:
                    invoice_list.append(invoice_id)
                    invoice = invoice_obj.browse(cr, uid, invoice_id)
                    partner_id = invoice.partner_id.id
                    account_id = invoice.account_id.id
                    if invoice.amount_total - invoice_amount:
                        warnings += _("\nWARNING: Invoice %s and its payment have a difference %f,") % (invoice.number, invoice.amount_total - invoice_amount)
                    if invoice.move_id:
                        cr.execute("select id from account_move_line l where account_id in (select id from account_account where type in ('payable', 'receivable') and active) and reconcile_id is null and move_id=%s" % invoice.move_id.id)
                        res = cr.fetchall()
                        if len(res):
                            if config.activate_insert:
                                reconcile_id = statement_reconcile_obj.create(cr, uid, {
                                    'line_ids': [(6, 0, map(lambda x:x[0], res))]
                                    }, context=context)
            else:
                partner_id = False
                reconcile_id = False
                account_id = type_payment == 'customer' and account_receivable or account_payable
                warnings += _("\nWARNING: Partner Bank %s not found,") % (partner_bank_name)

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
            }
            values.update(self.epassporte_payment_line_fields(row)) # Adds additional fields or updates fields
            if config.activate_insert:
                statement_line_obj.create(cr, uid, values, context=context)

            if type_payment == 'customer':
                debit_payment -= amount_payment
            else:
                credit_payment += amount_payment

            self.epassporte_extra_info(cr, uid, row, config, context=context)
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


# -*- encoding: utf-8 -*-
#
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
##############################################################################
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
from report import report_sxw
from tools import config
from tools.translate import _

class VATReportPaymentReportFull(report_sxw.rml_parse):
	_name = 'report.account.vat.declaration.full'
	def __init__(self, cr, uid, name, context):
		super(VATReportPaymentReportFull, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_codes': self._get_codes,
			'get_company': self._get_company,
			'get_currency': self._get_currency,
			'get_lines' : self._get_lines,
		})
        def _create_tax_code_dict_full(self,cr,uid,context):
            tax_list = {}
            if self.pool.get('account.tax.code')._get_company(cr, uid, context):
                tax_code_obj_list = self.pool.get('account.tax.code').search(cr, uid, ['company_id','=',context['company_id']])
            else:
                tax_code_obj_list = self.pool.get('account.tax.code').search(cr, uid, [])

            for tax_id in tax_code_obj_list:
                full_obj = { 'amount' : 0.0,
                    'invoices_link' : [],
                    }
                tax_list[tax_id] = full_obj
            ## Add Specific id to 0 for untaxes amount
            full_obj = { 'amount' : 0.0,
                'invoices_link' : [],
                }
            tax_list[0] = full_obj
            return tax_list
        ## This function compute tax based on invoice for an range of date

        def _construct_full_line(self,form,datee):
            ### Get all line concerned
            context = {'date_from': form['date_from'],'date_to':form['date_to'],'company_id':form['company_id']}
            tax_code_obj = self.pool.get('account.tax.code')
            ids = tax_code_obj.search(self.cr, self.uid, [('company_id','=',context['company_id'])])
            tax_obj = self.pool.get('account.tax.code')
            thier_lines = tax_obj.getthirdpartylines(self.cr,self.uid,ids,datee,context)
            tax_dict = self._create_tax_code_dict_full(self.cr, self.uid, context)
            for line in thier_lines:
                ## Compute payment for this line
                if line['debit'] != 0.0:
                    tmp_base_amount = abs(line['debit'])
                else:
                    tmp_base_amount = abs(line['credit'])

                payment_total = tax_obj.getpaymentforaline(self.cr, self.uid, line,datee)
                prorata = tax_obj.compute_prorate(tmp_base_amount,payment_total)
                for prodline  in tax_obj.getlinefortax(self.cr,self.uid,context,line):
                    if prodline['debit']  != 0.0:
                        amount_tax = 0 - abs(prodline['debit'])
                    else:
                        amount_tax = abs(prodline['credit'])
                    ## Get invoice for move_if one
                    invoice_obj = self.pool.get('account.invoice')
                    invoice_ids = invoice_obj.search(self.cr,self.uid,[('move_id','=',prodline['move_id'])])
                    if invoice_ids:
                        invoice_number = invoice_obj.browse(self.cr,self.uid,invoice_ids)[0].number
                    else:
                        invoice_number = ''
                    ##
                    ## Get partner name for move_if one
                    partner_obj = self.pool.get('res.partner')
                    if prodline['partner_id']:
                        partner_name = partner_obj.browse(self.cr,self.uid,[prodline['partner_id']])[0].name
                    else:
                        partner_name = ''
                    ##
                    ## Get move name for move_if one
                    move_obj = self.pool.get('account.move')
                    if prodline['move_id']:
                        move_name = move_obj.browse(self.cr,self.uid,[prodline['move_id']])[0].name
                    else:
                        move_name = ''
                    ##
                    prod_val = { 'name' : prodline['name'],
                    'move_name' : move_name,
                    'prorat_amount' : round(amount_tax * prorata, int(config['price_accuracy'])),
                    'prorata': str(round(prorata * 100, int(config['price_accuracy']))) + '%',
                    'invoice' : invoice_number,
                    'partner' : partner_name
                    }
                    prodline['vat_prorata_amount'] =  amount_tax * prorata
                    if tax_dict.has_key(prodline['tax_code_id']) :
                        tax_dict[prodline['tax_code_id']]['amount'] = tax_dict[prodline['tax_code_id']]['amount'] + amount_tax * prorata
                        tax_dict[prodline['tax_code_id']]['invoices_link'].append(prod_val)
                    else:
                        tax_dict[0]['amount'] = tax_dict[0]['amount'] + amount_tax * prorata
                        tax_dict[0]['invoices_link'].append(prod_val)
            for record in tax_code_obj.browse(self.cr, self.uid, ids, context):
                def _rec_get(record):
                    if tax_dict.has_key(record.id):
                        amount =  tax_dict[record.id]['amount']
                    else:
                        amount = 0.0
                    for rec in record.child_ids:
                        amount += _rec_get(rec) * rec.sign
                    return amount
                tax_dict[record.id]['amount'] = round(_rec_get(record), int(config['price_accuracy']))

            return tax_dict
	def _get_lines(self,form,company_id=False, parent=False, level=0):
            ### Get Result
            list_code = self._get_codes(company_id, parent, level)
            tc = self.pool.get('account.tax.code')
            if form['date_to_from'] == 'date_to':
                ThirdParty = self._construct_full_line(form,form['date_to'])
            else:
                ThirdParty = self._construct_full_line(form,form['date_from'])
            result = []
            for id_tab in list_code:
                ##
                tax_info = tc.browse(self.cr, self.uid, id_tab[1])
                #print str(list_code[id])
                res_pot = {
                   'name':tax_info.name,
                   'level' : id_tab[0],
                   'amount':ThirdParty[id_tab[1]]['amount'],
                   'invoice_link' :ThirdParty[id_tab[1]]['invoices_link']
                }
                result.append(res_pot)
                ##
            ## Add amount without tax
            res_pot_without_tax = {
                   'name':_('Amount without VAT'),
                   'level' : id_tab[0],
                   'amount': ThirdParty[0]['amount'],
                   'invoice_link' :ThirdParty[0]['invoices_link']
                }
            result.append(res_pot_without_tax)

            return result


	def _get_codes(self, company_id, parent=False, level=0):
		tc = self.pool.get('account.tax.code')
		ids = tc.search(self.cr, self.uid, [('parent_id','=',parent),('company_id','=',company_id)])

		res = []
		for code in tc.browse(self.cr, self.uid, ids):
			res.append(('.'*2*level,code.id))

			res += self._get_codes(company_id, code.id, level+1)
		return res


	def _get_company(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).name

	def _get_currency(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.name




report_sxw.report_sxw('report.account.vat.payment.declaration.full', 'account.tax.code',
	'addons/c2c_cash_based_vat_report/report/vat_report_payment_full.rml', parser=VATReportPaymentReportFull, header=False)


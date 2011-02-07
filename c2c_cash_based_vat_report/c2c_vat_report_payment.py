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

from osv import fields
from osv import osv
import time
from datetime import date
from tools import config

class VATReportPayment(osv.osv):
    _name = "account.tax.code"
    _inherit = "account.tax.code"
    ## this function create an empty dict to sotare taxes
    def _create_tax_code_dict(self,cr,uid,context):
        tax_list = {}
        if self._get_company(cr, uid, context):
            tax_code_obj_list = self.pool.get('account.tax.code').search(cr, uid, ['company_id','=',context['company_id']])
        else:
            tax_code_obj_list = self.pool.get('account.tax.code').search(cr, uid, [])

        for tax_id in tax_code_obj_list:
            tax_list[tax_id] = 0.0
        ## Add Specific id to 0 for untaxes amount
        tax_list[0] = 0.0
        return tax_list
    ## This function compute tax based on invoice for an range of date
    def _sum_invoice_date_fnc(self,cr,uid,ids,date_from,date_to,context):
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
        acc_set = ",".join(map(str, ids2))
        cr.execute("SELECT line.tax_code_id, sum(line.tax_amount) \
                FROM account_move_line AS line \
                WHERE line.tax_code_id in ("+acc_set+") and date between '"+ str(date_from) +"' and '" + str(date_to) +  "'  \
                " + self._get_company(cr, uid, context)  + " \
                GROUP BY line.tax_code_id")
        res=dict(cr.fetchall())
        for record in self.browse(cr, uid, ids, context):
            def _rec_get(record):
                amount = res.get(record.id, 0.0)
                for rec in record.child_ids:
                    amount += _rec_get(rec) * rec.sign
                return amount
            res[record.id] = round(_rec_get(record), int(config['price_accuracy']))

        ids_full = self.search(cr, uid,[])
        tax_result = self._create_tax_code_dict(cr, uid,context)
        for id in ids_full:
            if res.has_key(id):
                tax_result[id] = res[id]
        return tax_result
    # tHIS function test if the line is a credit note, a invoice
    def is_a_reconcile_creditnote(self,cr,uid,record_move_line,context):
        ### this function test if we need to check this line, it prevent to not take refund twice
        
        account_obj = self.pool.get('account.account')
        account_payable_list = account_obj.search(cr, uid, [('type','=','payable'),('company_id','=',context['company_id'])])
        account_receivable_list = account_obj.search(cr, uid, [('type','=','receivable'),('company_id','=',context['company_id'])])
        ## This line is a credit note to manage because is unreconcile, so we need to add to open amount
        if record_move_line['account_id'] in account_receivable_list and record_move_line['credit'] > 0.0 and not (record_move_line['reconcile_id'] or record_move_line['reconcile_partial_id']) :
            return True
        ## This line is a supplier credit note to manage because is unreconcile, so we need to add to open amount
        elif record_move_line['account_id'] in account_payable_list and record_move_line['debit'] > 0.0 and not (record_move_line['reconcile_id'] or record_move_line['reconcile_partial_id']) :
            return True
        ## this line is an supplier invoice line
        elif record_move_line['account_id'] in account_payable_list and record_move_line['credit'] > 0.0 :
            return True
        ## This line is an invoice line
        elif record_move_line['account_id'] in account_receivable_list and record_move_line['debit'] > 0.0 :
            return True
        else:
            return False

    def getthirdpartylines(self,cr,uid,ids,date,context):
        ## We will search the third party of line that we need to check
        cr.execute(" select st_full.id,st_full.name,st_full.journal_id,st_full.account_id,st_full.move_id,st_full.debit,st_full.credit,st_full.reconcile_id,st_full.reconcile_partial_id from account_move_line as st_full where st_full.id in ( \
                    select st.id from account_move_line as st where \
                        st.reconcile_id in \
                    (select al.reconcile_id from account_move_line as al where \
                        al.date >= '" + str(date)  + "') \
                    UNION ALL \
                    select st2.id from account_move_line as st2 where \
                            st2.reconcile_id is null \
                    UNION ALL \
                    select st3.id from account_move_line as st3 where \
                            st3.reconcile_partial_id is not null \
                   )  and st_full.date <= '" + str(date)  + "'  \
                      and  st_full.account_id in (select id from account_account where type in ('receivable','payable') ) \
                      and st_full.journal_id in (select id from account_journal where type in ('purchase','sale')) \
                      and st_full.account_id = 58\
                      " + self._get_company(cr, uid, context))

        ## Now we have all invoice supplier an fournisseur linked with invoice
        res=cr.dictfetchall()
        return res

    def getpaymentforaline(self,cr,uid,res_id,date):
        ## We search payment in case of full reconcile or  partial reconcile
        if res_id['reconcile_id']:
            cr.execute("select * from account_move_line where id <> " + str(res_id['id']) +  " and reconcile_id =" + str(res_id['reconcile_id']) + " and date <= '" + str(date)  + "' ")
            invoice_payment = cr.dictfetchall()
        elif res_id['reconcile_partial_id']:
            cr.execute("select * from account_move_line where id <> " + str(res_id['id']) +  " and reconcile_partial_id =" + str(res_id['reconcile_partial_id']) + " and date <= '" + str(date)  + "' ")
            invoice_payment = cr.dictfetchall()
        else:
            invoice_payment = []
        ## Get record to get amount of payment
        payment_total = 0.0
        for payment in invoice_payment:
            ## We will compute the residual for this invoice
            ##Store line captured for debug purpose
            if payment['debit'] != 0.0:
                pay_amount = abs(payment['debit'])
            else:
                pay_amount = abs(payment['credit'])
            payment_total = payment_total + pay_amount
        ##
        return payment_total
    def compute_prorate(self,base_amount,payment):
        ## We now compute the prorata
        if base_amount != 0.0:
            prorata = (base_amount - payment) / base_amount
        else:
            prorata = 0.0
        if prorata < 0.0002:
            prorata = 0.0
        return prorata
    def getlinefortax(self,cr,uid,context,res_id):
        ## Get tax line linked with a specific move_id
        cr.execute("select * from account_move_line where id <> " + str(res_id['id']) + " and move_id =" + str(res_id['move_id']) )
        full_line_notvat = cr.dictfetchall()
        return full_line_notvat

    def compute_tax_table(self,cr,uid,context,res_id,prorata,tax_dict):
        ## We will now search all line linked with a specific move
        
        full_line_notvat = self.getlinefortax(cr, uid, context, res_id)
#        import pdb
#        pdb.set_trace()
        ## We will now search prorata
        #
        for line_vatexc in full_line_notvat:
            ## Compute
            ##Store line captured for debug purpose
            #
            if line_vatexc['debit']  != 0.0:
                amount_tax = 0 - abs(line_vatexc['debit'])
            else:
                amount_tax = abs(line_vatexc['credit'])
            line_vatexc['vat_prorata_amount'] =  amount_tax * prorata
            if tax_dict.has_key(line_vatexc['tax_code_id']) :
                print str(line_vatexc['tax_code_id'])
                tax_dict[line_vatexc['tax_code_id']] = tax_dict[line_vatexc['tax_code_id']] + amount_tax * prorata
            else:
                tax_dict[0] = tax_dict[0] + amount_tax * prorata
            print str(tax_dict)
        #
        ##
        return tax_dict

    def sum_date_fnc(self,cr,uid,ids,date,context):
        ## We create an array to stare taxes
        #tax_dict = self._create_tax_code_dict(cr, uid,context).copy()
        ## We will search
        res = self.getthirdpartylines(cr, uid, ids, date, context)
        ## Now we have all invoice supplier an fournisseur linked with invoice
        tax_dict = self._create_tax_code_dict(cr, uid,context).copy()
        for res_id in res:
            #
            if self.is_a_reconcile_creditnote(cr,uid,res_id,context):

                if res_id['debit'] != 0.0:
                    tmp_base_amount = abs(res_id['debit'])
                else:
                    tmp_base_amount = abs(res_id['credit'])

                payment_total = self.getpaymentforaline(cr,uid, res_id,date)
                prorata = self.compute_prorate(tmp_base_amount,payment_total)
                tax_dict = self.compute_tax_table(cr, uid, context, res_id,prorata,tax_dict).copy()
        tax_code_obj = self.pool.get('account.tax.code')
        print str(tax_dict)
        for record in tax_code_obj.browse(cr, uid, ids, context):
            def _rec_get(record):
                amount = tax_dict.get(record.id, 0.0)
                for rec in record.child_ids:
                    amount += _rec_get(rec) * rec.sign
                return amount
            tax_dict[record.id] = round(_rec_get(record), int(config['price_accuracy']))
        #print str(line_captured)
        return tax_dict

    def _sum_date1(self, cr, uid, ids, name, args, context):
        ## Get tax amount for start date
        if 'date_from' in context and context['date_from']:
            datee = context['date_from']
        else:
            datee = date.today()
        return self.sum_date_fnc(cr, uid,ids,datee,context)

    def _sum_date2(self, cr, uid, ids, name, args, context):
        ## Get tax amount for end date
        if 'date_to' in context and context['date_to']:
            datee = context['date_to']
        else:
            datee = date.today()
        return self.sum_date_fnc(cr, uid,ids,datee,context)

    def _sum_date_invoice_based(self, cr, uid, ids, name, args, context):
        ## Get tax amount bases on invoice between start date and end_date
        if 'date_to' in context and context['date_to']:
            date_from = context['date_from']
            date_to = context['date_to']
        else:
            date_from = date.today()
            date_to = date.today()
        return self._sum_invoice_date_fnc(cr, uid,ids,date_from,date_to,context)

    def _get_company(self,cr,uid,context):
        if self.pool.get('account.move.line').__dict__['_columns'].has_key('company_id'):
            return " and company_id = " + str(context['company_id'])
        else:
            return ''

    def _compute_vat(self, cr, uid, ids, name, args, context):

        dict_global = self._create_tax_code_dict(cr, uid,context)
        p1 = self._sum_date1(cr, uid, ids, name, args, context)
        print str(p1)
        p2 = self._sum_date2(cr, uid, ids, name, args, context)
        sum_inv = self._sum_date_invoice_based(cr, uid, ids, name, args, context)
        ids_full = self.search(cr, uid,[])
        ids_full.append(0)
        dict_final = self._create_tax_code_dict(cr,uid,context)
        for id in ids_full:
            dict_final[id] = sum_inv[id] + p1[id] - p2[id]
            elem = { 'sum_p1' : p1[id],
                    'sum_p2' : p2[id],
                    'sum_period_date' : sum_inv[id],
                    'sum_diff_total' : dict_final[id],
            }
            dict_global[id] = elem

        return dict_global

    _columns = {
        'sum_p1': fields.function(_compute_vat, method=True, string="+ Open Amt. Begin", multi='vat_cpt'),
        'sum_p2': fields.function(_compute_vat, method=True, string="- Open Amt. End", multi='vat_cpt'),
        'sum_period_date': fields.function(_compute_vat, method=True, string="+ Invoices", multi='vat_cpt'),
        'sum_diff_total': fields.function(_compute_vat, method=True, string="= Cash Bas. Inv.", multi='vat_cpt'),
    }



VATReportPayment()

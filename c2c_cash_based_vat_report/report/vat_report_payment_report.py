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
from tools.translate import _

class VATReportPaymentReport(report_sxw.rml_parse):
	_name = 'report.account.vat.declaration'
	def __init__(self, cr, uid, name, context):
		super(VATReportPaymentReport, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'get_codes': self._get_codes,
			'get_company': self._get_company,
			'get_currency': self._get_currency,
			'get_lines' : self._get_lines,
		})


	def _get_lines(self,form,company_id=False, parent=False, level=0):
            ### Get Result
            list_code = self._get_codes(company_id, parent, level)
            tc = self.pool.get('account.tax.code')
            ids = tc.search(self.cr, self.uid, [('company_id','=',company_id)])
            context = {'date_from': form['date_from'],'date_to':form['date_to'],'company_id':form['company_id']}
            resultat = self.pool.get('account.tax.code')._compute_vat(self.cr, self.uid,ids,'', {},context)
            result = []
            for id_tab in list_code:
                ##
                tax_info = tc.browse(self.cr, self.uid, id_tab[1])
                #print str(list_code[id])
                res_pot = {
                   'name':tax_info.name,
                   'level' : id_tab[0],
                   'P1':resultat[id_tab[1]]['sum_p1'],
                   'P2':resultat[id_tab[1]]['sum_p2'],
                   'period_date':resultat[id_tab[1]]['sum_period_date'],
                   'sum_vat':resultat[id_tab[1]]['sum_diff_total'],
                }
                result.append(res_pot)
                ##
            ## Add amount without tax
            res_pot_without_tax = {
               'name':_('Amount without VAT'),
               'level' : '',
               'P1':resultat[0]['sum_p1'],
               'P2':resultat[0]['sum_p2'],
               'period_date':resultat[0]['sum_period_date'],
               'sum_vat':resultat[0]['sum_diff_total'],
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




report_sxw.report_sxw('report.account.vat.payment.declaration', 'account.tax.code',
	'addons/c2c_vat_report_payment/report/vat_report_payment.rml', parser=VATReportPaymentReport, header=False)


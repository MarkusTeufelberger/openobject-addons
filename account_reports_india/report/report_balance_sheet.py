# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
import pooler
import time
import mx.DateTime
from report import report_sxw
from account_reports_india.report import report_pl_account

class report_balancesheet(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_balancesheet, self).__init__(cr, uid, name, context)
        self.obj_pl=report_pl_account.report_pl_account(cr, uid, name, context)
        self.result_sum_dr=0.0
        self.result_sum_lib_dr=0.0
        self.result_sum_cr=0.0
        self.result_sum_ass_cr=0.0
        self.result_dr=0.0
        self.result_cr=0.0
        self.final=[]
        self.localcontext.update({
            'time': time,
            'get_lines' : self.get_lines,
            'get_company': self.get_company,
            'get_currency': self._get_currency,
            'sum_dr' : self.sum_dr,
            'sum_cr' : self.sum_cr,
            'get_acc_obj':self.get_acc_obj,
            'get_data':self.get_data,
            'sum_lib_dr' : self.sum_lib_dr,
            'sum_ass_cr' : self.sum_ass_cr,
            'sum_lib1_dr' : self.sum_lib1_dr,
            'sum_ass1_cr' : self.sum_ass1_cr,

            
        })
        self.context = context
        
    def sum_dr(self):
        return self.result_sum_dr or 0.0
     
    def sum_cr(self):
        return self.result_sum_cr or 0.0
    
    def sum_lib_dr(self):
        return self.result_sum_lib_dr or 0.0
     
    def sum_ass_cr(self):
        return self.result_sum_ass_cr or 0.0
    
    def sum_lib1_dr(self):
        return self.result_dr or 0.0
     
    def sum_ass1_cr(self):
        return self.result_cr or 0.0

    
    def get_data(self,form):
        gr_list=['liability','asset']
        res_pl={}
        result_pl=self.obj_pl.get_data(form)
        res_pl=self.obj_pl.final_result()
        if res_pl['type']== 'Net Profit':
            res_pl['balance'] *= -1
        total_list=['Share Holder/Owner Fund','Branch/Division','Loan(Liability) Account','Current Liabilities','Suspense Account','Fixed Assets','Investment','Current Assets','Misc. Expenses(Asset)']
        resp={}
        for group in gr_list: 
            if group=='liability':
                list_acc=['Share Holder/Owner Fund','Branch/Division','Loan(Liability) Account','Current Liabilities','Suspense Account']
            if group=='asset':
                list_acc=['Fixed Assets','Investment','Current Assets','Misc. Expenses(Asset)']
            acc_objs=[]
            final_result={}
            result=[]
            result_temp=[]
            res={}
            acc_ids=[]
            context  = self.context.copy()
            context['fiscalyear'] = context={'fiscalyear': form['fiscalyear']}
            fiscalyear_obj =  pooler.get_pool(self.cr.dbname).get('account.fiscalyear')
            date_obj=fiscalyear_obj.browse(self.cr, self.uid, context['fiscalyear'])
            year_start_date = date_obj.date_start
            year_end_date = date_obj.date_stop  
            comp_ids=[]
            c_child_ids=pooler.get_pool(self.cr.dbname).get('res.company')._get_company_children(self.cr, self.uid,form['company_id'])
            if c_child_ids:
                comp_ids = c_child_ids
            else:
                comp_ids.append(form['company_id'])
            for lacc in list_acc:
                acc_ids +=self.pool.get('account.account').search(self.cr, self.uid, [('name','=', lacc),('company_id','in',comp_ids)])
            if form['display_type'] == 'consolidated':
                ids2= acc_ids
            else:
                ids2 = self.pool.get('account.account')._get_children_and_consol(self.cr, self.uid, acc_ids, context)
            acc_objs=self.pool.get('account.account').browse(self.cr, self.uid, ids2)
            balance_dict=self.pool.get('account.account').compute_total(self.cr,self.uid,ids2,year_start_date,year_end_date,form['date1'],form['date2'],{'debit': 0.0,'credit': 0.0, 'balance': 0.0})
            for aobj in acc_objs:
                res={}
                res['name']=aobj.name
                res['balance']=balance_dict[aobj.id]['balance']
                res['type']=aobj.user_type.code
                res['level']=aobj.level
                if res['level']== False:
                    if aobj.parent_id:
                        for r in result:
                            if r['name']== aobj.parent_id.name:
                                res['level'] = r['level'] + 1
                                break
                if res['level'] > 4:
                    res['outer']='-1'
                    if res['type'] == 'liability':
                         self.result_dr +=res['balance']
                    else:
                         self.result_cr +=res['balance']

                if res['level']== 4:
                    res['outer']='0'
                    if res['type'] == 'liability':
                         self.result_sum_lib_dr +=res['balance']
                    else:
                         self.result_sum_ass_cr +=res['balance']

                if res['level']== 3:
                    res['outer']='1'
                    if res['type'] == 'liability':
                        self.result_sum_dr +=res['balance']
                    else:
                        self.result_sum_cr +=res['balance']
                if res_pl['type']=='Net Profit' and res['name']=='Reserve & Surplus Account':
                    resp['outer']='-1'
                    resp['name']= res_pl['type']
                    resp['type']=res['type']
                    resp['level']=res['level'] + 1
                    resp['balance']=res_pl['balance']
                    self.result_sum_lib_dr +=resp['balance']
                    self.result_sum_dr +=resp['balance']
                    self.result_dr +=resp['balance']
                    res['balance'] += resp['balance']
                if res_pl['type']=='Net Loss' and res['name']=='Misc. Expenses(Asset)':
                    resp['outer']='0'
                    resp['name']= res_pl['type']
                    resp['type']=res['type']
                    resp['level']=res['level'] +1
                    resp['balance']=res_pl['balance']
                    self.result_sum_ass_cr +=resp['balance']
                    self.result_sum_cr +=resp['balance']
                    res['balance'] += resp['balance']
                if form['empty_account']==False and res['name'] not in total_list:
                    if res['balance']:
                        if form['display_type'] == 'consolidated':
                            if res['name'] in total_list:
                                result.append(res)  
                        else:
                            result.append(res) 
                else:
                    if form['display_type'] == 'consolidated':
                        if res['name'] in total_list:
                            result.append(res)  
                    else:
                        result.append(res) 
                if form['display_type'] == 'consolidated':
                    if res_pl['type']=='Net Profit' and res['name']=='Share Holder/Owner Fund':
                        resp['outer']='0'
                        resp['name']= res_pl['type']
                        resp['type']=res['type']
                        resp['level']=res['level'] + 1
                        resp['balance']=res_pl['balance']
                        result.append(resp)
                        self.result_sum_lib_dr +=resp['balance']
                        self.result_sum_dr +=resp['balance']
                        res['balance'] += resp['balance']
                if res_pl['type']=='Net Profit' and res['name']=='Reserve & Surplus Account':
                    for rt in result:
                        if rt['name']== 'Share Holder/Owner Fund':
                            rt['balance'] += resp['balance']
                    result.append(resp)
                if res_pl['type']=='Net Loss' and res['name']=='Misc. Expenses(Asset)':
                    result.append(resp)
                final_result['gr_name']=group
                final_result['list']=result
                self.final.append(final_result)
        return None
    
    def get_acc_obj(self,obj_list,group):
        result=[]
        for obj_acc in obj_list:
            if obj_acc.type == group:
                result.append(obj_acc)       
        return result

    def get_lines(self,group):
        result=[]
        for list in self.final:
            if list['gr_name']== group:
                result=list['list']
        return result
    
    def _get_currency(self, form):
        return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.code

    def get_company(self,form):
        comp_obj=pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr,self.uid,form['company_id'])
        return comp_obj.name 

report_sxw.report_sxw('report.account.balancesheet', 'account.account',
    'addons/account_reports_india/report/report_balance_sheet.rml',parser=report_balancesheet,
    header=False)

# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Vincent Renaville
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
from mx.DateTime import *
from report import report_sxw
import xml
import rml_parse
import pooler
import calendar
import mx.DateTime 
from datetime import datetime



class order_annexe(rml_parse.rml_parse):
    # def preprocess(self, objects, data, ids):
    #   # new_ids = self.pool.get('account.invoice').search(self.cr, self.uid,
    #   #            [('type','=','out_invoice'),('state', 'in', ['paid','open']),('date_invoice','>=',data['form']['date_start']),('date_invoice','<=',data['form']['date_end'])])
    #   #        objects = self.pool.get('account.invoice').browse(self.cr, self.uid, new_ids)
    #   
    #   #Look
    #   
    #   data['form']['date_start']=(mx.DateTime.strptime(data['form']['date_start'], "%Y-%m-%d")).strftime("%d.%m.%Y")
    #   data['form']['date_end']=(mx.DateTime.strptime(data['form']['date_end'], "%Y-%m-%d")).strftime("%d.%m.%Y")
    #   super(list_of_invoices_c2c, self).preprocess(objects, data, new_ids)
    
    def __init__(self, cr, uid, name, context):
        super(order_annexe, self).__init__(cr, uid, name, context)
        self.user_obj = self.pool.get('res.users').browse(self.cr, self.uid,self.uid)
        self.localcontext.update( {
            'pages': self.pages,
            'swiss_date' : self._get_and_change_date_format_for_swiss,
            'strip_name':self._explode_name,
        })
        self.context = context

    def compute_amount_in_currency(self,amount,currency,date):
        context_up = {
        'date': date,
        }
        subtotalincurrency = self.pool.get('res.currency').compute(self.cr,self.uid,self.user_obj.company_id.currency_id.id,currency,amount,context_up)
        return subtotalincurrency
    
    def compute_amount_from_pricelist(self,price_list,prod_id,qty,date,partner_id=None):
        context_up = {
        'date': date,
        }
        subtotalincurrency = self.pool.get('product.pricelist').price_get(self.cr, self.uid, [price_list.id], prod_id, qty, partner_id, context_up)[price_list.id]
        return subtotalincurrency

    # Compute for each product (in each line), the linked options
    def pages(self, sale):
        context=self.context
        result=[]
        for line in sale.order_line:
            product_page={}
            # Construct page infos
            product_page['order_ref']=sale.name
            sale_date = mx.DateTime.strptime(sale.date_order, "%Y-%m-%d")
            product_page['date_order']=sale_date.strftime("%d.%m.%Y")
            product_page['currency']=sale.pricelist_id.currency_id.name
            product_page['product_name']=self.pool.get('product.product').name_get(self.cr,self.uid,[line.product_id.id],context)[0][1]
            # product_page['product_name']=line.product_id.name_get(self.cr, self.uid, [line.product_id.id], context)[0][1]
            # Construct line infos
            lines = []
            for prod in line.product_id.product_options_id:
                date = sale_date.strftime("%Y-%m-%d")
                price_computed=self.compute_amount_from_pricelist(sale.pricelist_id,prod.id,1,date,sale.partner_id.id)
                lines.append({'code':prod.code,'name':prod.name,'price':price_computed})
                # lines.append({'code':prod.code,'name':prod.name,'price':price_computed})
            product_page['lines']=lines
            # If it exists some options -> print it, otherwise not
            if len(lines)>0:
                result.append(product_page)
        if result == []:
            return False
        else:
            return result
        

report_sxw.report_sxw('report.c2c_annexe_order.annexe_order','sale.order','addons/c2c_annexe_order/report/order_annexe.rml',parser=order_annexe)

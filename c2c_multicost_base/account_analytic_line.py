# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camtocamp SA
# @author Joël Grand-Guillaume
# $Id: $
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

from osv import fields
from osv import osv
from tools.translate import _

from tools import config

class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'

    def _amount_currency(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            cmp_cur_id=rec.company_id.currency_id.id
            aa_cur_id=rec.account_id.currency_id.id
            # Always provide the amount in currency
            if cmp_cur_id != aa_cur_id:
                cur_obj = self.pool.get('res.currency')
                ctx = {}
                if rec.date and rec.amount:
                    ctx['date'] = rec.date
                    result[rec.id] = cur_obj.compute(cr, uid, rec.company_id.currency_id.id,
                        rec.account_id.currency_id.id, rec.amount,
                        context=ctx)
            else:
                result[rec.id]=rec.amount
        return result
        
    def _get_account_currency(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            # Always provide second currency
            result[rec.id] = (rec.account_id.currency_id.id,rec.account_id.currency_id.code)
        return result
    
    def _get_account_line(self, cr, uid, ids, context={}):
        aac_ids = {}
        for acc in self.pool.get('account.analytic.account').browse(cr, uid, ids):
            aac_ids[acc.id] = True
        aal_ids = []
        if aac_ids:
            aal_ids = self.pool.get('account.analytic.line').search(cr, uid, [('account_id','in',aac_ids.keys())], context=context)
        return aal_ids

    _columns = {
          'currency_id': fields.function(_get_account_currency, method=True, type='many2one', relation='res.currency', string='Account currency',
                  store={
                      'account.analytic.account': (_get_account_line, ['company_id'], 50),
                      'account.analytic.line': (lambda self,cr,uid,ids,c={}: ids, ['amount','unit_amount'],10),
                  },
                  help="The related account currency if not equal to the company one."),
          'company_id': fields.many2one('res.company','Company',required=True),
          'amount_currency': fields.function(_amount_currency, method=True, digits=(16, int(config['price_accuracy'])), string='Amount currency',
                  store={
                      'account.analytic.account': (_get_account_line, ['company_id'], 50),
                      'account.analytic.line': (lambda self,cr,uid,ids,c={}: ids, ['amount','unit_amount'],10),
                  },
                  help="The amount expressed in the related account currency if not equal to the company one."),
    }
    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    # Compute the cost based on the price type define into company
    # property_valuation_price_type property
    def on_change_unit_amount(self, cr, uid, id, prod_id, unit_amount,company_id,
            unit=False, context=None):
        if context==None:
            context={}
        uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        company_obj=self.pool.get('res.company')
        if  prod_id:
            prod = product_obj.browse(cr, uid, prod_id)
            a = prod.product_tmpl_id.property_account_expense.id
            if not a:
                a = prod.categ_id.property_account_expense_categ.id
            if not a:
                raise osv.except_osv(_('Error !'),
                        _('There is no expense account defined ' \
                                'for this product: "%s" (id:%d)') % \
                                (prod.name, prod.id,))
            if not company_id:
                company_id=company_obj._company_default_get(cr, uid, 'account.analytic.line', context)

            # Compute based on pricetype
            pricetype=self.pool.get('product.price.type').browse(cr,uid,company_obj.browse(cr,uid,company_id).property_valuation_price_type.id)
            # Take the company currency as the reference one
            context['currency_id']=company_obj.browse(cr,uid,company_id).currency_id.id
            amount_unit=prod.price_get(pricetype.field, context)[prod.id]
            amount=amount_unit*unit_amount or 1.0
            return {'value': {
                'amount': - round(amount, 2),
                'general_account_id': a,
                }}
        return {}
    
account_analytic_line()
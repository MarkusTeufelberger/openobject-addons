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
import operator

from osv import fields
from osv import osv


class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    def _compute_currency_for_level_tree(self, cr, uid, ids, ids2, res, acc_set, context={}):
        # Handle multi-currency on each level of analytic account
        # This is a refactoring of _balance_calc computation
        cr.execute("SELECT a.id, r.currency_id FROM account_analytic_account a INNER JOIN res_company r ON (a.company_id = r.id) where a.id in (%s)" % acc_set)
        currency= dict(cr.fetchall())
        res_currency= self.pool.get('res.currency')
        for id in ids:
            if id not in ids2:
                continue
            for child in self.search(cr, uid, [('parent_id', 'child_of', [id])]):
                if child != id:
                    res.setdefault(id, 0.0)
                    if  currency[child]!=currency[id]:
                        res[id] += res_currency.compute(cr, uid, currency[child], currency[id], res.get(child, 0.0), context=context)
                    else:
                        res[id] += res.get(child, 0.0)

        cur_obj = res_currency.browse(cr,uid,currency.values(),context)
        cur_obj = dict([(o.id, o) for o in cur_obj])
        for id in ids:
            if id in ids2:
                res[id] = res_currency.round(cr,uid,cur_obj[currency[id]],res.get(id,0.0))

        return dict([(i, res[i]) for i in ids ])


    def _credit_calc(self, cr, uid, ids, name, arg, context={}):
        res = {}
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
        acc_set = ",".join(map(str, ids2))
        
        for i in ids:
            res.setdefault(i,0.0)
            
        if not ids2:
            return res
            
        where_date = ''
        if context.get('from_date',False):
            where_date += " AND l.date >= '" + context['from_date'] + "'"
        if context.get('to_date',False):
            where_date += " AND l.date <= '" + context['to_date'] + "'"
        cr.execute("SELECT a.id, COALESCE(SUM(l.amount_currency),0) FROM account_analytic_account a LEFT JOIN account_analytic_line l ON (a.id=l.account_id "+where_date+") WHERE l.amount_currency<0 and a.id =ANY(%s) GROUP BY a.id",(ids2,))
        r = dict(cr.fetchall())
        return self._compute_currency_for_level_tree(cr, uid, ids, ids2, r, acc_set, context)
        
    def _debit_calc(self, cr, uid, ids, name, arg, context={}):
        res = {}
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
        acc_set = ",".join(map(str, ids2))
        
        for i in ids:
            res.setdefault(i,0.0)
            
        if not ids2:
            return res
        
        where_date = ''
        if context.get('from_date',False):
            where_date += " AND l.date >= '" + context['from_date'] + "'"
        if context.get('to_date',False):
            where_date += " AND l.date <= '" + context['to_date'] + "'"
        cr.execute("SELECT a.id, COALESCE(SUM(l.amount_currency),0) FROM account_analytic_account a LEFT JOIN account_analytic_line l ON (a.id=l.account_id "+where_date+") WHERE l.amount_currency>0 and a.id =ANY(%s) GROUP BY a.id" ,(ids2,))
        r= dict(cr.fetchall())
        return self._compute_currency_for_level_tree(cr, uid, ids, ids2, r, acc_set, context)
        
    def _balance_calc(self, cr, uid, ids, name, arg, context={}):
        res = {}
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
        acc_set = ",".join(map(str, ids2))
        
        for i in ids:
            res.setdefault(i,0.0)
            
        if not ids2:
            return res
        
        where_date = ''
        if context.get('from_date',False):
            where_date += " AND l.date >= '" + context['from_date'] + "'"
        if context.get('to_date',False):
            where_date += " AND l.date <= '" + context['to_date'] + "'"
        cr.execute("SELECT a.id, COALESCE(SUM(l.amount_currency),0) FROM account_analytic_account a LEFT JOIN account_analytic_line l ON (a.id=l.account_id "+where_date+") WHERE a.id =ANY(%s) GROUP BY a.id",(ids2,))
        
        for account_id, sum in cr.fetchall():
            res[account_id] = sum

        return self._compute_currency_for_level_tree(cr, uid, ids, ids2, res, acc_set, context)

    def _get_account_currency(self, cr, uid, ids, field_name, arg, context={}):
        result=self._get_company_currency(cr, uid, ids, field_name, arg, context={})
        return result
   
    _columns = {
        'balance' : fields.function(_balance_calc, method=True, type='float', string='Balance'),
        'debit' : fields.function(_debit_calc, method=True, type='float', string='Debit'),
        'credit' : fields.function(_credit_calc, method=True, type='float', string='Credit'),
        'currency_id': fields.function(_get_account_currency, method=True, type='many2one', relation='res.currency', string='Account currency', store=True),
    }

account_analytic_account()

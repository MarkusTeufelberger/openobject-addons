# -*- encoding: utf-8 -*-
#  account.py
#  c2c_multi_currency_consolidated_chart
#  Created by Camptocamp
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
####################################################################
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
from osv import fields, osv
from tools import config

class AccountAccount(osv.osv):
    _inherit = "account.account"
    #we ooveride the function instead of using super for performance purposese
    def __compute(self, cr, uid, ids, field_names, arg, context={}, query=''):
        #compute the balance/debit/credit accordingly to the value of field_name for the given account ids

        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance ",
            'debit': "COALESCE(SUM(l.debit), 0) as debit ",
            'credit': "COALESCE(SUM(l.credit), 0) as credit "
        }
        res_currency_obj =  self.pool.get('res.currency')
        accounts = {}
        #get all the necessary accounts
        global_ids = []
        for current_acc_id in ids :
            ids2 = self._get_children_and_consol(cr, uid, [current_acc_id], context)
            global_ids += ids2
            acc_set = ",".join(map(str, ids2))
            #compute for each account the balance/debit/credit from the move lines
            if ids2:
                aml_query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
                wheres = []
                if query.strip():
                    wheres.append(query.strip())
                if aml_query.strip():
                    wheres.append(aml_query.strip())
                query = " AND ".join(wheres)
                sql = """SELECT comp.currency_id as currid, %s 
                FROM  (account_move_line as l INNER JOIN account_account as acc on (l.account_id = acc.id))
                INNER JOIN res_company as comp on(acc.company_id = comp.id)
                WHERE l.account_id IN (%s)   
                AND %s
                GROUP BY l.account_id, comp.currency_id;""" %( ' , '.join(map(lambda x: mapping[x], field_names)),
                                                              acc_set,
                                                              query,
                                                             )
 
                cr.execute(sql)
                account_res = {'debit': 0.0, 'credit': 0.0, 'balance':0.0 }
                current_acc = self.browse(cr, uid, current_acc_id)
                result = cr.dictfetchall()
                current_currency = current_acc.company_id.currency_id.id
                for res in result:
                    # if the currency of some lines are not the same
                    #of the current account we convert them to the current account currency
                    if res['currid'] != current_currency :
                        res['debit'] = res_currency_obj.compute(
                                                                            cr, 
                                                                            uid, 
                                                                            res['currid'],
                                                                            current_currency, 
                                                                            res['debit'], 
                                                                            round=False,
                                                                            context=context,
                                                                        )
                        res['credit'] = res_currency_obj.compute(
                                                                            cr, 
                                                                            uid, 
                                                                            res['currid'],
                                                                            current_currency, 
                                                                            res['credit'], 
                                                                            round=False,
                                                                            context=context,
                                                                        )  
                      
                        res['balance'] =  res['debit'] - res['credit']
                    account_res['debit'] += res['debit']
                    account_res['credit'] += res['credit']
                    account_res['balance'] += res['balance']
                    
                accounts[current_acc_id] = account_res
        # consolidate accounts with direct children
        global_ids = list(set(global_ids))
        brs = list(self.browse(cr, uid, global_ids, context=context))
        sums = {}
        while brs:
            current = brs[0]
            can_compute = True
            for child in current.child_id:
                if child.id not in sums:
                    can_compute = False
                    try:
                        brs.insert(0, brs.pop(brs.index(child)))
                    except ValueError:
                        brs.insert(0, child)
            if can_compute:
                brs.pop(0)
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    if current.child_id:
                        sums[current.id][fn] += sum(sums[child.id][fn] for child in current.child_id)
        res = {}
        null_result = dict((fn, 0.0) for fn in field_names)
        for id in ids:
            res[id] = sums.get(id, null_result)
        return res

        #algo trouver toutes les lignes enfants les sorter par currency
        #calculer debit, credit, balance dans le currency de la company du compte en cours
        
    _columns ={
        'balance': fields.function(__compute, digits=(16, int(config['price_accuracy'])), method=True, string='Balance', multi='balance'),
        'credit': fields.function(__compute, digits=(16, int(config['price_accuracy'])), method=True, string='Credit', multi='balance'),
        'debit': fields.function(__compute, digits=(16, int(config['price_accuracy'])), method=True, string='Debit', multi='balance'),
    }
        
AccountAccount()
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
import time
import pooler
from report import report_sxw

class aged_trial_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(aged_trial_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_lines': self._get_lines,
            'get_total': self._get_total,
            'get_before': self._get_before,
            'get_for_period': self._get_for_period,
            'get_company': self._get_company,
            'get_currency': self._get_currency,
        })

    def _add_header(self, node):
        return True

    def _get_lines(self, form):
        res = []

        if form['category'] == 'Customer' or form['category'] == 'Supplier' :
            cat_id=pooler.get_pool(self.cr.dbname).get('res.partner.category').search(self.cr,self.uid,[('name','=',form['category'])])
            cat_id+=pooler.get_pool(self.cr.dbname).get('res.partner.category').search(self.cr,self.uid,[('parent_id','child_of',cat_id)])
        else:
            cat_id=pooler.get_pool(self.cr.dbname).get('res.partner.category').search(self.cr,self.uid,[('name','in',['Customer','Supplier'])])
            cat_id+=pooler.get_pool(self.cr.dbname).get('res.partner.category').search(self.cr,self.uid,[('parent_id','child_of',cat_id)])

        self.cr.execute('SELECT partner_id from res_partner_category_rel where category_id in ('+','.join(map(str,cat_id))+')')
        data=self.cr.fetchall()
        self.partner_ids=[]
        self.partner_ids=list(set([x[0] for x in data]))

        account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
        line_query = account_move_line_obj._query_get(self.cr, self.uid, obj='line',
                context={'fiscalyear': form['fiscalyear']})
        self.cr.execute("SELECT DISTINCT res_partner.id AS id, " \
                    "res_partner.name AS name " \
                "FROM res_partner, account_move_line AS line, account_account " \
                "WHERE (line.account_id=account_account.id) " \
                    "AND (line.reconcile_id IS NULL) " \
                    "AND (line.partner_id=res_partner.id) " \
                    "AND " + line_query + " " \
                    "AND (account_account.company_id = %s) " \
                    "AND account_account.active " \
                    "AND partner_id in ("+','.join(map(str,self.partner_ids))+")" \
                "ORDER BY res_partner.name", (form['company_id'],))
        partners = self.cr.dictfetchall()
        for partner in partners:
            values = {}
            self.cr.execute("SELECT SUM(debit-credit) " \
                    "FROM account_move_line AS line, account_account " \
                    "WHERE (line.account_id=account_account.id) " \
                        "AND (account_account.type IN ('payable','receivable')) " \
                        "AND (date < %s) AND (partner_id=%s) " \
                        "AND (reconcile_id IS NULL) " \
                        "AND " + line_query + " " \
                        "AND (account_account.company_id = %s) " \
                        "AND account_account.active",
                        (form['0']['start'], partner['id'], form['company_id']))
            before = self.cr.fetchone()
            values['before'] = before and before[0] or ""
            for i in range(5):
                self.cr.execute("SELECT SUM(debit-credit) " \
                        "FROM account_move_line AS line, account_account " \
                        "WHERE (line.account_id=account_account.id) " \
                            "AND (account_account.type IN ('payable','receivable')) " \
                            "AND (date >= %s) AND (date <= %s) " \
                            "AND (partner_id = %s) " \
                            "AND (reconcile_id IS NULL) " \
                            "AND " + line_query + " " \
                            "AND (account_account.company_id = %s) " \
                            "AND account_account.active",
                            (form[str(i)]['start'], form[str(i)]['stop'],
                                partner['id'], form['company_id']))
                during = self.cr.fetchone()
                values[str(i)] = during and during[0] or ""

            self.cr.execute("SELECT SUM(debit-credit) " \
                    "FROM account_move_line AS line, account_account " \
                    "WHERE (line.account_id = account_account.id) " \
                        "AND (account_account.type IN ('payable','receivable')) " \
                        "AND (partner_id = %s) " \
                        "AND (reconcile_id IS NULL) " \
                        "AND " + line_query + " " \
                        "AND (account_account.company_id = %s) " \
                        "AND account_account.active",
                        (partner['id'], form['company_id']))
            total = self.cr.fetchone()
            values['total'] = total and total[0] or 0.0
            values['name'] = partner['name']
            t = 0.0
            for i in range(5)+['before']:
                t+= float(values.get(str(i), 0.0) or 0.0)
            if values['total']:
                res.append(values)
        total = 0.0
        totals = {}
        for r in res:
            total += float(r['total'] or 0.0)
            for i in range(5)+['before']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res

    def _get_total(self, fiscalyear, company_id):
        account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
        line_query = account_move_line_obj._query_get(self.cr, self.uid, obj='line',
                context={'fiscalyear': fiscalyear})
        self.cr.execute("SELECT SUM(debit - credit) " \
                "FROM account_move_line AS line, account_account " \
                "WHERE (line.account_id = account_account.id) " \
                    "AND (account_account.type IN ('payable', 'receivable')) "\
                    "AND reconcile_id IS NULL " \
                    "AND partner_id is NOT NULL " \
                    "AND " + line_query + " " \
                    "AND (account_account.company_id = %s) " \
                    "AND partner_id in ("+','.join(map(str,self.partner_ids))+")" \
                    "AND account_account.active",
                    (company_id,))
        total = self.cr.fetchone()
        return total and total[0] or 0.0

    def _get_before(self, date, fiscalyear, company_id):
        account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
        line_query = account_move_line_obj._query_get(self.cr, self.uid, obj='line',
                context={'fiscalyear': fiscalyear})
        self.cr.execute("SELECT SUM(debit - credit) " \
                "FROM account_move_line AS line, account_account " \
                "WHERE (line.account_id = account_account.id) " \
                    "AND (account_account.type IN ('payable', 'receivable')) " \
                    "AND reconcile_id IS NULL " \
                    "AND (date < %s) " \
                    "AND partner_id IS NOT NULL " \
                    "AND " + line_query + " " \
                    "AND (account_account.company_id = %s) " \
                    "AND partner_id in ("+','.join(map(str,self.partner_ids))+")" \
                    "AND account_account.active",
                    (date, company_id))
        before = self.cr.fetchone()
        return before and before[0] or 0.0

    def _get_for_period(self, period, fiscalyear, company_id):
        account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
        line_query = account_move_line_obj._query_get(self.cr, self.uid, obj='line',
                context={'fiscalyear': fiscalyear})
        self.cr.execute("SELECT SUM(debit - credit) " \
                "FROM account_move_line AS line, account_account " \
                "WHERE (line.account_id = account_account.id) " \
                    "AND (account_account.type IN ('payable', 'receivable')) " \
                    "AND reconcile_id IS NULL " \
                    "AND (date >= %s) " \
                    "AND (date <= %s) " \
                    "AND partner_id IS NOT NULL " \
                    "AND " + line_query + " " \
                    "AND (account_account.company_id = %s) " \
                    "AND partner_id in ("+','.join(map(str,self.partner_ids))+")" \
                    "AND account_account.active",
                    (period['start'], period['stop'], company_id))
        period = self.cr.fetchone()
        return period and period[0] or 0.0

    def _get_company(self, form):
        return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).name

    def _get_currency(self, form):
        return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.name

report_sxw.report_sxw(
    'report.aged.trial.balance',
    'res.partner',
    'addons/cci_account/report/aged_trial_balance.rml',
    parser=aged_trial_report, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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

from lxml import etree
from osv import fields, osv


class AccountReportGeneralLedgerWizard(osv.osv_memory):
    """Will launch general ledger report and pass required args"""

#    _inherit = "account.common.account.report"
    _name = "account.report.general.ledger.webkit"
    _description = "General Ledger Report"

    def _get_account_ids(self, cr, uid, context=None):
        res = False
        if context.get('active_model', False) == 'account.account' and context.get('active_ids', False):
            res = context['active_ids']
        return res

    _columns = {
        'initial_balance': fields.boolean("Include initial balances",
                                          help='It adds initial balance row'),

        'amount_currency': fields.boolean("With Currency",
                                          help="It adds the currency column"),

        'display_account': fields.selection([('bal_all', 'All'),
                                             ('bal_mix', 'With transactions or non zero balance')],
                                            'Display accounts',
                                            required=True),
        'account_ids': fields.many2many('account.account', 'wiz_account_rel',
                                        'account_id', 'wiz_id', 'Filter on accounts',
                                         help="Only selected accounts will be printed. Leave empty to print all accounts."),

        # backport : as we cannot inherit osv_memory in v5 we have to copy the code from the inherited objects of v6 (account.common.report, account.common.account.report)
        'chart_account_id': fields.many2one('account.account', 'Chart of account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)]),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year', help='Keep empty for all open fiscal year'),
        'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True),
        'period_from': fields.many2one('account.period', 'Start period'),
        'period_to': fields.many2one('account.period', 'End period'),
#        'journal_ids': fields.many2many('account.journal', 'account_common_journal_rel', 'account_id', 'journal_id', 'Journals', required=True), # unused
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
    }

    def _get_account(self, cr, uid, context=None):
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return accounts and accounts[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False

    def _get_all_journal(self, cr, uid, context=None):
        return self.pool.get('account.journal').search(cr, uid ,[])
    
    _defaults = {
        'amount_currency': lambda *a: False,
        'initial_balance': lambda *a: True,
        'display_account': lambda *a: 'bal_mix',
        'account_ids': _get_account_ids,
        'fiscalyear_id': _get_fiscalyear,
        'journal_ids': _get_all_journal,
        'filter': lambda *a: 'filter_no',
        'chart_account_id': _get_account,
        'target_move': lambda *a: 'posted',
    }

    def onchange_fiscalyear(self, cursor, uid, ids, fiscalyear=False, context=None):
        res = {}
        if not fiscalyear:
            res['value'] = {'initial_balance': False}
        return res

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # GTK client problem onchange does not consider in save record
        if not data['form']['fiscalyear_id']:
            data['form'].update({'initial_balance': False})
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_general_ledger_webkit',
                'datas': data}


    # backport : as we cannot inherit osv_memory in v5 we have to copy the code from the inherited objects of v6 (account.common.report, account.common.account.report)
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        res = super(AccountReportGeneralLedgerWizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar)
        if context.get('active_model', False) == 'account.account' and view_id:
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='chart_account_id']")
            for node in nodes:
                node.set('readonly', '1')
                node.set('help', 'If you print the report from Account list/form view it will not consider Charts of account')
            res['arch'] = etree.tostring(doc)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {}
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': False ,'date_to': False}
        if filter == 'filter_date':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': time.strftime('%Y-01-01'), 'date_to': time.strftime('%Y-%m-%d')}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.special = false
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND p.special = false
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods =  [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['fiscalyear'] = 'fiscalyear_id' in data['form'] and data['form']['fiscalyear_id'] or False
        result['chart_account_id'] = 'chart_account_id' in data['form'] and data['form']['chart_account_id'] or False
        if data['form']['filter'] == 'filter_date':
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to']
        elif data['form']['filter'] == 'filter_period':
            if not data['form']['period_from'] or not data['form']['period_to']:
                raise osv.except_osv(_('Error'),_('Select a starting and an ending period'))
            result['period_from'] = data['form']['period_from']
            result['period_to'] = data['form']['period_to']
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from',  'date_to',  'fiscalyear_id', 'period_from',
                                                'period_to',  'filter',  'chart_account_id', 'target_move',
                                                'initial_balance', 'amount_currency', 'display_account',
                                                'account_ids'])[0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = used_context
        return self._print_report(cr, uid, ids, data, context=context)

AccountReportGeneralLedgerWizard()

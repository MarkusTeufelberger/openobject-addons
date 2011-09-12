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
from tools.translate import _


class AccountReportPartnersLedgerWizard(osv.osv_memory):
    """Will launch partner ledger report and pass required args"""

#    _inherit = "account.common.partner.report"
    _name = "account.report.partners.ledger.webkit"
    _description = "Partner Ledger Report"

    _columns = {
        'initial_balance': fields.boolean("Include initial balances",
                                          help='It adds initial balance row'),
        'amount_currency': fields.boolean("With Currency",
                                          help="It adds the currency column"),
        'exclude_reconciled': fields.boolean("Exclude reconciled entries",
                                             help="TODO"),
        'until_date': fields.date("Report date",
                                  required=True,
                                  help="Allows you to excludes entries reconciled between the end date of the report and this date' ; generally used for audit/provisionning purposes."),
        'partner_ids': fields.many2many('res.partner', 'wiz_part_rel',
                                        'partner_id', 'wiz_id', 'Filter on partner',
                                         help="Only selected partners will be printed. Leave empty to print all partners."),
        'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True, help='Filter by date : no opening balance will be displayed. (opening balance can only be calculated based on period to be correct).'),

        # backport : as we cannot inherit osv_memory in v5 we have to copy the code from the inherited objects of v6 (account.common.report, account.common.account.report)
        'display_account': fields.selection([('bal_all','All'), ('bal_movement','With movements'),
                                            ('bal_solde','With balance is not equal to 0'),
                                            ],'Display accounts', required=True),
        'chart_account_id': fields.many2one('account.account', 'Chart of account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)]),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year', help='Keep empty for all open fiscal year'),
        'period_from': fields.many2one('account.period', 'Start period'),
        'period_to': fields.many2one('account.period', 'End period'),
#        'journal_ids': fields.many2many('account.journal', 'account_common_journal_rel', 'account_id', 'journal_id', 'Journals', required=True),  # unused
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
        'result_selection': fields.selection([('customer','Receivable Accounts'),
                                              ('supplier','Payable Accounts'),
                                              ('customer_supplier','Receivable and Payable Accounts')],
                                              "Partner's", required=True),
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
        'exclude_reconciled': lambda *a: True,
        'result_selection': lambda *a: 'customer_supplier',
        'display_account': lambda *a: 'bal_all',
        'fiscalyear_id': _get_fiscalyear,
        'journal_ids': _get_all_journal,
        'filter': lambda *a: 'filter_no',
        'chart_account_id': _get_account,
        'target_move': lambda *a: 'posted',
    }

    def _check_until_date(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'period_to', 'date_to', 'until_date'], context=context)
        min_date = self.default_until_date(cr, uid, ids, obj['fiscalyear_id'], obj['period_to'], obj['date_to'], context=context)
        if min_date and obj['until_date'] < min_date:
            return False
        return True

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'filter'], context=context)
        if not obj['fiscalyear_id'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_until_date, 'Clearance date is too early.', ['until_date']),
        (_check_fiscalyear, 'When no Fiscal year is selected, you must choose to filter by periods or by date.', ['filter']),
    ]

    def default_until_date(self, cursor, uid, ids, fiscalyear_id=False, period_id=False, date_to=False, context=None):
        res_date = False
        # first priority: period or date filters
        if period_id:
            res_date = self.pool.get('account.period').read(cursor, uid, period_id, ['date_stop'], context=context)['date_stop']
        elif date_to:
            res_date = date_to
        elif fiscalyear_id:
            res_date = self.pool.get('account.fiscalyear').read(cursor, uid, fiscalyear_id, ['date_stop'], context=context)['date_stop']

        return res_date

    def onchange_fiscalyear(self, cursor, uid, ids, fiscalyear=False, period_id=False, date_to=False, until_date=False, context=None):
        res = {'value': {}}
        if not fiscalyear:
            res['value']['initial_balance'] = False
        res['value']['until_date'] = self.default_until_date(cursor, uid, ids,
                                                             fiscalyear_id=fiscalyear,
                                                             period_id=period_id,
                                                             date_to=date_to,
                                                             context=context)
        return res

    def onchange_date_to(self, cursor, uid, ids, fiscalyear=False, period_id=False, date_to=False, until_date=False, context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(cursor, uid, ids,
                                                             fiscalyear_id=fiscalyear,
                                                             period_id=period_id,
                                                             date_to=date_to,
                                                             context=context)
        return res

    def onchange_period_to(self, cursor, uid, ids, fiscalyear=False, period_id=False, date_to=False, until_date=False, context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(cursor, uid, ids,
                                                             fiscalyear_id=fiscalyear,
                                                             period_id=period_id,
                                                             date_to=date_to,
                                                             context=context)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = super(AccountReportPartnersLedgerWizard, self).onchange_filter(cr, uid, ids, filter=filter, fiscalyear_id=fiscalyear_id, context=context)
        if res.get('value', False):
            res['value']['until_date'] = self.default_until_date(cr, uid, ids,
                                                                 fiscalyear_id=fiscalyear_id,
                                                                 period_id=res['value'].get('period_to', False),
                                                                 date_to=res['value'].get('date_to', False),
                                                                 context=context)
        return res

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # GTK client problem onchange does not consider in save record
        if not data['form']['fiscalyear_id'] or data['form']['filter'] == 'filter_date':
            data['form'].update({'initial_balance': False})
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_partners_ledger_webkit',
                'datas': data}

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
        data['form'] = self.read(cr, uid, ids, ['date_from',  'date_to',  'fiscalyear_id', 'journal_ids',
                                                'period_from', 'period_to',  'filter', 'chart_account_id',
                                                'target_move', 'initial_balance', 'amount_currency', 'partner_ids',
                                                'until_date', 'exclude_reconciled', 'result_selection'])[0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = used_context
        return self._print_report(cr, uid, ids, data, context=context)

AccountReportPartnersLedgerWizard()

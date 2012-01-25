# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
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

from account_report_balance_common import previous_year_date

class AccountTrialBalanceWizard(osv.osv_memory):
    """Will launch trial balance report and pass required args"""

#    _inherit = "account.common.balance.report"
    _name = "account.report.trial.balance.webkit"
    _description = "Trial Balance Report"

    COMPARISON_LEVEL = 3

    COMPARE_SELECTION = [('filter_no', 'No Comparison'),
                         ('filter_year', 'Fiscal Year'),
                         ('filter_date', 'Date'),
                         ('filter_period', 'Periods'),
                         ('filter_opening', 'Opening Only')]

    _columns = {

        # from account.common.balance.report
        'account_ids': fields.many2many('account.account', 'wiz_account_rel',
                                        'account_id', 'wiz_id', 'Filter on accounts',
                                         help="Only selected accounts will be printed. Leave empty to print all accounts."),
        'filter': fields.selection([('filter_no', 'No Filters'),
                                    ('filter_date', 'Date'),
                                    ('filter_period', 'Periods'),
                                    ('filter_opening', 'Opening Only')], "Filter by", required=True, help='Filter by date : no opening balance will be displayed. (opening balance can only be calculated based on period to be correct).'),

        # from account.common.account.report
        'display_account': fields.selection([('bal_all','All'), ('bal_movement','With movements'),
                                            ('bal_solde','With balance is not equal to 0'),
                                            ],'Display accounts', required=True),

        # from account.common.report
        'chart_account_id': fields.many2one('account.account', 'Chart of account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)]),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year', help='Keep empty for all open fiscal year'),
        'period_from': fields.many2one('account.period', 'Start period'),
        'period_to': fields.many2one('account.period', 'End period'),
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
    }

    def _get_account_ids(self, cr, uid, context=None):
        res = False
        if context.get('active_model', False) == 'account.account' and context.get('active_ids', False):
            res = context['active_ids']
        return res

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
        'account_ids': _get_account_ids,
        'display_account': lambda *a: 'bal_all',

        'fiscalyear_id': _get_fiscalyear,
        'journal_ids': _get_all_journal,
        'filter': lambda *a: 'filter_no',
        'chart_account_id': _get_account,
        'target_move': lambda *a: 'posted',

        # hardcoded because in v5 default_get overwrites the selection when we confirm the wizard :-(
        'comp0_filter': lambda *a: 'filter_no',
        'comp1_filter': lambda *a: 'filter_no',
        'comp2_filter': lambda *a: 'filter_no',
    }

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'filter'], context=context)
        if not obj['fiscalyear_id'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_fiscalyear, 'When no Fiscal year is selected, you must choose to filter by periods or by date.', ['filter']),
    ]

    def default_get(self, cr, uid, fields, context=None):
        """
             To get default values for the object.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param fields: List of fields for which we want default values
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        res = super(AccountTrialBalanceWizard, self).default_get(cr, uid, fields, context=context)
        # hardcoded in _defaults because in v5 default_get overwrites the selection when we confirm the wizard :-(
#        for index in range(self.COMPARISON_LEVEL):
#            field = "comp%s_filter" % (index,)
#            if not res.get(field, False):
#                res[field] = 'filter_no'
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        res = super(AccountTrialBalanceWizard, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar)

        for index in range(self.COMPARISON_LEVEL):
            # create columns for each comparison page
            self._columns.update({
                "comp%s_filter" % (index,):
                    fields.selection(self.COMPARE_SELECTION,
                                     string="Compare By",
                                     required=True),
                "comp%s_fiscalyear_id" % (index,):
                    fields.many2one('account.fiscalyear', 'Fiscal year'),
                "comp%s_period_from" % (index,):
                    fields.many2one('account.period', 'Start period'),
                "comp%s_period_to" % (index,):
                    fields.many2one('account.period', 'End period'),
                "comp%s_date_from" % (index,):
                    fields.date("Start Date"),
                "comp%s_date_to" % (index,):
                    fields.date("End Date"),
            })

        eview = etree.fromstring(res['arch'])
        placeholder = eview.xpath("//page[@string='placeholder']")
        if placeholder:
            placeholder = placeholder[0]
            for index in range(self.COMPARISON_LEVEL):
                # add fields
                res['fields']["comp%s_filter" % (index,)] = {'string': "Compare By", 'type': 'selection', 'selection': self.COMPARE_SELECTION, 'required': True}
                res['fields']["comp%s_fiscalyear_id" % (index,)] = {'string': "Fiscal Year", 'type': 'many2one', 'relation': 'account.fiscalyear'}
                res['fields']["comp%s_period_from" % (index,)] = {'string': "Start Period", 'type': 'many2one', 'relation': 'account.period'}
                res['fields']["comp%s_period_to" % (index,)] = {'string': "End Period", 'type': 'many2one', 'relation': 'account.period'}
                res['fields']["comp%s_date_from" % (index,)] = {'string': "Start Date", 'type': 'date'}
                res['fields']["comp%s_date_to" % (index,)] = {'string': "End Date", 'type': 'date'}

                page = etree.Element('page', {'name': "comp%s" % (index,), 'string': _("Comparison %s") % (index+1,)})
                page.append(etree.Element('field', {'name': "comp%s_filter" % (index,),
                                                    'colspan': '4',
                                                    'on_change': "onchange_comp_filter(%(index)s, filter, comp%(index)s_filter, fiscalyear_id, date_from, date_to)" % {'index': index}}))
                page.append(etree.Element('field', {'name': "comp%s_fiscalyear_id" % (index,),
                                                    'colspan': '4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','in',('filter_year','filter_opening'))], 'readonly':[('comp%(index)s_filter','not in',('filter_year','filter_opening'))]}" % {'index': index}}))
                page.append(etree.Element('separator', {'string': _('Dates'), 'colspan':'4'}))
                page.append(etree.Element('field', {'name': "comp%s_date_from" % (index,), 'colspan':'4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_date')], 'readonly':[('comp%(index)s_filter','!=','filter_date')]}" % {'index': index}}))
                page.append(etree.Element('field', {'name': "comp%s_date_to" % (index,), 'colspan':'4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_date')], 'readonly':[('comp%(index)s_filter','!=','filter_date')]}" % {'index': index}}))
                page.append(etree.Element('separator', {'string': _('Periods'), 'colspan':'4'}))
                page.append(etree.Element('field', {'name': "comp%s_period_from" % (index,),
                                                    'colspan': '4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_period')], 'readonly':[('comp%(index)s_filter','!=','filter_period')]}" % {'index': index},
                                                    'domain': "[('special', '=', False)]"}))
                page.append(etree.Element('field', {'name': "comp%s_period_to" % (index,),
                                                    'colspan': '4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_period')], 'readonly':[('comp%(index)s_filter','!=','filter_period')]}" % {'index': index},
                                                    'domain': "[('special', '=', False)]"}))

                placeholder.addprevious(page)
            placeholder.getparent().remove(placeholder)

            if context.get('active_model', False) == 'account.account' and view_id:
                nodes = eview.xpath("//field[@name='chart_account_id']")
                for node in nodes:
                    node.set('readonly', '1')
                    node.set('help', 'If you print the report from Account list/form view it will not consider Charts of account')
                res['arch'] = etree.tostring(eview)
        res['arch'] = etree.tostring(eview)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {}
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': False ,'date_to': False}
        if filter == 'filter_date':
            if fiscalyear_id:
                fyear = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear_id, context=context)
                date_from = fyear.date_start
                date_to = fyear.date_stop > time.strftime('%Y-%m-%d') and time.strftime('%Y-%m-%d') or fyear.date_stop
            else:
                date_from, date_to = time.strftime('%Y-01-01'), time.strftime('%Y-%m-%d')
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': date_from, 'date_to': date_to}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods =  [i[0] for i in cr.fetchall()]
            if periods:
                start_period = end_period = periods[0]
                if len(periods) > 1:
                    end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res

    def onchange_comp_filter(self, cr, uid, ids, index, main_filter='filter_no', comp_filter='filter_no', fiscalyear_id=False, start_date=False, stop_date=False, context=None):
        res = {}
        fy_obj = self.pool.get('account.fiscalyear')
        last_fiscalyear_id = False
        if fiscalyear_id:
            fiscalyear = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
            last_fiscalyear_ids = fy_obj.search(cr, uid, [('date_stop', '<', fiscalyear.date_start)],
                                                limit=self.COMPARISON_LEVEL, order='date_start desc', context=context)
            if last_fiscalyear_ids:
                if len(last_fiscalyear_ids) > index:
                    last_fiscalyear_id = last_fiscalyear_ids[index]  # first element for the comparison 1, second element for the comparison 2

        fy_id_field = "comp%s_fiscalyear_id" % (index,)
        period_from_field = "comp%s_period_from" % (index,)
        period_to_field = "comp%s_period_to" % (index,)
        date_from_field = "comp%s_date_from" % (index,)
        date_to_field = "comp%s_date_to" % (index,)

        if comp_filter == 'filter_no':
            res['value'] = {fy_id_field: False, period_from_field: False, period_to_field: False, date_from_field: False ,date_to_field: False}
        if comp_filter in ('filter_year', 'filter_opening'):
            res['value'] = {fy_id_field: last_fiscalyear_id, period_from_field: False, period_to_field: False, date_from_field: False ,date_to_field: False}
        if comp_filter == 'filter_date':
            dates = {}
            if main_filter == 'filter_date':
                dates = {
                    'date_start': previous_year_date(start_date, index + 1).strftime('%Y-%m-%d'),
                    'date_stop': previous_year_date(stop_date, index + 1).strftime('%Y-%m-%d'),}
            elif last_fiscalyear_id:
                dates = fy_obj.read(cr, uid, last_fiscalyear_id, ['date_start', 'date_stop'], context=context)

            res['value'] = {fy_id_field: False, period_from_field: False, period_to_field: False, date_from_field: dates.get('date_start', False), date_to_field: dates.get('date_stop', False)}
        if comp_filter == 'filter_period' and last_fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %(fiscalyear)s
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %(fiscalyear)s
                               AND p.date_start < NOW()
                               AND COALESCE(p.special, FALSE) = FALSE
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', {'fiscalyear': last_fiscalyear_id})
            periods =  [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = end_period = periods[0]
                if len(periods) > 1:
                    end_period = periods[1]
            res['value'] = {fy_id_field: False, period_from_field: start_period, period_to_field: end_period, date_from_field: False, date_to_field: False}
        return res

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['fiscalyear'] = 'fiscalyear_id' in data['form'] and data['form']['fiscalyear_id'] or False
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
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

    def pre_print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        fields_to_read = ['account_ids', 'display_account', 'date_from',
                          'date_to', 'fiscalyear_id', 'journal_ids', 'period_from',
                          'period_to',  'filter',  'chart_account_id', 'target_move']

        # comparison fields
        for index in range(self.COMPARISON_LEVEL):
            fields_to_read.extend([
                "comp%s_filter" % (index,),
                "comp%s_fiscalyear_id" % (index,),
                "comp%s_period_from" % (index,),
                "comp%s_period_to" % (index,),
                "comp%s_date_from" % (index,),
                "comp%s_date_to" % (index,),])

        vals = self.read(cr, uid, ids,
                         fields_to_read,
                         context=context)[0]
        vals['max_comparison'] = self.COMPARISON_LEVEL
        return vals

    def _print_report(self, cursor, uid, ids, data, context=None):
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_trial_balance_webkit',
                'datas': data}

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.pre_print_report(cr, uid, ids, context=context)
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = used_context
        return self._print_report(cr, uid, ids, data, context=context)

AccountTrialBalanceWizard()

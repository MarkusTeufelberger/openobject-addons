# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
import time
import math
import mx.DateTime
from tools.translate import _
from tools import config
#from mx.DateTime import RelativeDateTime, now, DateTime, localtime

class account_asset_category(osv.osv):
    _name = 'account.asset.category'
    _description = 'Asset category'
    _columns = {
        'code': fields.char('Asset Category Code', size=16, required=True, select=1),
        'name': fields.char('Asset Category', size=64, required=True, select=1),
        'note': fields.text('Note'),
        'parent_id': fields.many2one('account.asset.category', 'Parent Category'),
        'child_ids': fields.one2many('account.asset.category', 'parent_id', 'Children Categories'),

    }

    def _check_recursion(self, cr, uid, ids):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from account_asset_category where id in ('+','.join(map(str,ids))+')')
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True
    
    _constraints = [
        (_check_recursion, _('Error ! You can not create recursive categories.'), ['parent_id'])
    ]
account_asset_category()

class account_asset_asset(osv.osv):
    _name = 'account.asset.asset'
    _description = 'Asset'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for asset in self.browse(cr,uid,ids, context=context):
            res[asset.id] = {
                'amount_total': 0.0,
                'amount_residual': 0.0,
            }
            for method in asset.method_ids:
                res[asset.id]['amount_total'] += method.value_total
                res[asset.id]['amount_residual'] += method.value_residual
        return res


    def _get_method(self, cr, uid, ids, context=None):
        result = {}
        for method in self.pool.get('account.asset.method').browse(cr, uid, ids, context=context):
            result[method.asset_id.id] = True
        return result.keys()

    def _get_move_line(self, cr, uid, ids, context=None):
        result = {}
        for mline in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if mline.asset_method_id:
                result[mline.asset_method_id.asset_id.id] = True
        return result.keys()

    def clear(self, cr, uid, ids, context={}):
        for asset in self.browse(cr, uid, ids, context):
            ok = True
            for met in asset.method_ids:
                if met.state=='draft':
                    self.pool.get('account.asset.method').unlink(cr, uid, [met.id], context)
                elif met.state != 'close':
                    ok = False
            if ok:
                self.write(cr, uid, [asset.id], {'state':'close'}, context)
            else:
                raise osv.except_osv(_('Warning !'), _('This wizard works only when asset have just Draft and Closed methods !'))

        return True 

    _columns = {
        'name': fields.char('Asset', size=64, required=True, select=1),
        'code': fields.char('Asset Code', size=16, select=1, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'amount_total': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Total',
            store={
                'account.asset.asset': (lambda self, cr, uid, ids, c={}: ids, ['method_ids'], 20),
                'account.asset.method': (_get_method, ['value_total','value_residual','entry_ids','state'], 20),
                'account.move.line': (_get_move_line, ['debit','credit','account_id','asset_method_id'], 20),
            },
            multi='all'),
        'amount_residual': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Residual',
            store={
                'account.asset.asset': (lambda self, cr, uid, ids, c={}: ids, ['method_ids'], 20),
                'account.asset.method': (_get_method, ['value_total','value_residual','entry_ids','state'], 20),
                'account.move.line': (_get_move_line, ['debit','credit','account_id','asset_method_id'], 20),
           },
            multi='all'),

        'note': fields.text('Note'),
        'category_id': fields.many2one('account.asset.category', 'Asset Category', change_default=True),
        'localisation': fields.char('Localisation', size=32, select=2, readonly=True, states={'draft':[('readonly',False)]}, help = "Set this field before asset coonfirming. Later on you will have to use Change Localisation button."),
        'sequence': fields.integer('Seq.'),
        'date': fields.date('Date',readonly=True, states={'draft':[('readonly',False)]}, help = "Set this date or leave it empty to allow system set the first purchase date."),
        'state': fields.selection([('view','View'),('draft','Draft'),('normal','Normal'),('close','Closed')], 'Asset State', required=True, help = "Normal - Asset contains active methods (opened, suppressed or depreciated).\nClosed - Asset doesn't exist. All methods are sold or abandoned."),
        'active': fields.boolean('Active', select=2),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, states={'draft':[('readonly',False)]}, help = "If Date field is empty this field will be filled by first purchase."),
        'method_ids': fields.one2many('account.asset.method', 'asset_id', 'Asset Method Name', readonly=False, states={'close':[('readonly',True)]}),
        'history_ids': fields.one2many('account.asset.history', 'asset_id', 'History', readonly=True)
    }
    _defaults = {
        'code': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'account.asset.code'),
#        'date': lambda obj, cr, uid, context: time.strftime('%Y-%m-%d'),
        'active': lambda obj, cr, uid, context: True,
        'state': lambda obj, cr, uid, context: 'draft',
    }

    def unlink(self, cr, uid, ids, context={}):
        for obj in self.browse(cr, uid, ids, context):
            if obj.state != 'draft':
                raise osv.except_osv(_('Error !'), _('You can dalete assets only in Draft state !'))
        return super(account_asset_asset, self).unlink(cr, uid, ids, context)


    def _localisation(self, cr, uid, asset_id, localisation, name, note, context={}):
        asset = self.browse(cr, uid, asset_id, context)
        self.pool.get('account.asset.history').create(cr, uid, {
            'type': "transfer",
            'asset_id' : asset_id,
            'name': name,
#            'asset_total': asset.amount_total,
#            'asset_residual': asset.amount_residual,
            'note': _("Asset transfered to: ") + str(localisation)+ 
                    "\n" + str(note or ""),
        }, context)
        self.pool.get('account.asset.asset').write(cr, uid, [asset_id], {
            'localisation': localisation,
        }, context)
        return True

account_asset_asset()

class account_asset_method_type(osv.osv):
    _name = 'account.asset.method.type'
    _description = 'Asset Method Type'
    _columns = {
        'code': fields.char('Asset Method Type Code', size=16, required=True, select=1),
        'name': fields.char('Asset Method Type Name', size=64, required=True, select=1),
        'note': fields.text('Note'),
    }
account_asset_method_type()

class account_asset_method_defaults(osv.osv):
    _name = 'account.asset.method.defaults'
    _description = 'Asset Method Delfaults'
    _columns = {
        'asset_category': fields.many2one('account.asset.category', 'Asset Category', help = "Select the asset category for this set of defaults. If no selection defined defaults will concern to all methods of selected type."),
        'method_type': fields.many2one('account.asset.method.type', 'Method Type', required = True, help ="Select method type for this set of defaults.", ondelete = "cascade"),
        'account_asset_id': fields.many2one('account.account', 'Asset Account', help = "Select account used for cost basis of asset. It will be applied into invoice line when you select this asset in invoice line."),
        'account_expense_id': fields.many2one('account.account', 'Depr. Expense Account', help = "Select account used for depreciation expense (write-off). If you use direct method of depreciation this account should be the same as Asset Account."),
        'account_actif_id': fields.many2one('account.account', 'Depreciation Account',  help = "Select account used for depreciation amount."),
        'account_residual_id': fields.many2one('account.account', 'Sale Residual Account',  help = "Select account used for sale residual."),
        'account_impairment_id': fields.many2one('account.account', 'Impairment Account',  help = "Select account used for impairment amount. Used in revaluation."),
        'account_abandon_id': fields.many2one('account.account', 'Abandonment Account',  help = "Select account used for abandonment loss amount."),
        'journal_id': fields.many2one('account.journal', 'Journal', ),
        'journal_analytic_id': fields.many2one('account.analytic.journal', 'Analytic Journal'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'method': fields.selection([('linear','Straight-Line'), ('decbalance','Declining-Balance'), ('syd', 'Sum of Years Digits'),  ('uop','Units of Production'), ('progressive','Progressive')], 'Computation Method', ),
        'method_progress_factor': fields.float('Progressive factor', help = "Specify the factor of progression in depreciation. It is used in Declining-Balance method. When linear depreciation is 20% per year, and you want apply Double-Declining Balance you should choose Declining-Balance method and enter 0,40 (40%) as Progressive factor."),
#        'method_time': fields.selection([('interval','Interval'),('endofyear','End of Year')], 'Time Method'),
        'method_delay': fields.integer('Number of Intervals'),
        'method_period': fields.integer('Intervals per Year'),

    }

    _defaults = {
        'method': lambda obj, cr, uid, context: 'linear',
#        'method_time': lambda obj, cr, uid, context: 'interval',
        'method_progress_factor': lambda obj, cr, uid, context: 0.3,
        'method_delay': lambda obj, cr, uid, context: 5,
        'method_period': lambda obj, cr, uid, context: 1,
    }

account_asset_method_defaults()


class account_asset_method(osv.osv):              # Asset method = Asset Method
    def _amount_total(self, cr, uid, ids, name, args, context={}):
        if not ids:
            return {}
#        id_set=",".join(map(str,ids))
        res = {}
        for id in ids: #
            res[id] = {}

            method = self.browse(cr, uid, id, context)
            cr.execute("SELECT SUM(l.debit-l.credit) AS asset_acc_vals \
                            FROM account_asset_method p \
                            LEFT JOIN account_move_line l \
                                ON (p.id=l.asset_method_id) \
                            WHERE p.id = %s AND l.account_id = p.account_asset_id" % (id, ))
            asset_acc_val = cr.fetchone()[0] or 0.0

            if method.account_asset_id.id == method.account_expense_id.id:         # Direct method
                if (asset_acc_val == 0.0) and (method.state == 'close'):
                    write_off = 0.0
                else:
                    cr.execute("SELECT SUM(l.debit) AS writeoff \
                            FROM account_asset_method p \
                            LEFT JOIN account_move_line l \
                                ON (p.id=l.asset_method_id) \
                            WHERE p.id = %s AND p.account_actif_id = l.account_id" % (id, ))
                    write_off = cr.fetchone()[0] or 0.0
                res[id]['value_total'] = asset_acc_val + write_off
                res[id]['value_residual'] = asset_acc_val
            else:                                                       # Indirect method
                cr.execute("SELECT SUM(l.debit-l.credit) AS expense_acc_vals \
                            FROM account_asset_method p \
                            LEFT JOIN account_move_line l \
                                ON (p.id=l.asset_method_id) \
                            WHERE p.id = %s AND l.account_id = p.account_expense_id" % (id, ))

                expense_acc_val = cr.fetchone()[0] or 0.0
                res[id]['value_total'] = asset_acc_val
                res[id]['value_residual'] = asset_acc_val + expense_acc_val
        return res

    def _finish_depreciation(self, cr, uid, method, context={}):
        if method.state == 'open':
            self.write(cr, uid, [method.id], {
                'state': 'depreciated'
            })
            method.state='depreciated'
        return True

    def _close(self, cr, uid, method, context={}):
        if method.state<>'close':
            self.write(cr, uid, [method.id], {
                'state': 'close'
            })
            method.state='close'
        ok = (method.asset_id.state == 'normal')
        any_open = self.search(cr, uid, [('asset_id','=',method.asset_id.id),('state','<>','close')])
        if ok and not any_open:
            self.pool.get('account.asset.asset').write(cr, uid, [method.asset_id.id], {
                'state': 'close'
            }, context)
            method.asset_id.state='close'
        return True

    def _initial(self, cr, uid, method, period_id, date, base, expense, acc_impairment, intervals_before, name, note, context):
        period = self._check_date(cr, uid, period_id, date, context)
        self._post_3lines_move(cr, uid, method=method, period = period, date = date, \
                    acc_third_id = acc_impairment, base = base, expense = expense, method_initial = True, context = context)
        self.validate(cr, uid, [method.id], context)
        if not method.asset_id.date:
            self.pool.get('account.asset.asset').write(cr, uid, [method.asset_id.id], {
                'date': date,
            })
        if intervals_before:
            self.write(cr, uid, [method.id], {'intervals_before': intervals_before}, context)
        self.pool.get('account.asset.history')._history_line(cr, uid, "initial", method, name, \
                    base, expense, False, note, context)
        return True


    def _reval(self, cr, uid, method, period_id, date, base, expense, acc_impairment, name, note, context={}):
        period = self._check_date(cr, uid, period_id, date, context)
        direct = (method.account_asset_id.id == method.account_expense_id.id)
        expense = not direct and expense or False
        self._post_3lines_move(cr, uid, method = method, period = period, date = date, acc_third_id = acc_impairment, \
                    base = base, expense = expense, reval=True, context = context)
        self.pool.get('account.asset.history')._history_line(cr, uid, "reval", method, name, \
                    base, expense, False, note, context)
        return True

    def _abandon(self, cr, uid, methods, period_id, date, acc_abandon, name, note, context={}):
        period = self._check_date(cr, uid, period_id, date, context)
        for method in methods:
            if method.state in ['open','suppressed','depreciated']:
                direct = (method.account_asset_id.id == method.account_expense_id.id)
                base = not direct and -method.value_total or - method.value_residual 
                expense = not direct and -(method.value_total - method.value_residual) or False
                if base:
                    self._post_3lines_move(cr, uid, method = method, period = period, date = date, acc_third_id = acc_abandon, \
                        base = base, expense = expense, context = context)
                self.pool.get('account.asset.history')._history_line(cr, uid, "abandon", method, name,
                    base, expense, False, note, context)
                self._close(cr, uid, method, context)
        return True

    def _modif(self, cr, uid, method, method_delay, method_period, method_progress_factor, method_salvage, life, name, note, context={}):

        note2 = _("Changing of method parameters to:") + \
                    _('\n   Number of Intervals: ')+ str(method_delay) + \
                    _('\n   Intervals per Year: ')+ str(method_period) + \
                    _('\n   Progressive Factor: ') + str(method_progress_factor) + \
                    _('\n   Salvage Value: ') + str(method_salvage or 0.0)+ \
                    _('\n   Life Quantity: ') + str(life or 0.0)+ \
                    "\n" + str(note or "")

        self.pool.get('account.asset.history')._history_line(cr, uid, "change", method, name, 0.0, 0.0, False, note2, context )
        self.write(cr, uid, [method.id], {
            'method_delay': method_delay,
            'method_period': method_period,
            'method_progress_factor': method_progress_factor,
            'method_salvage': method_salvage,
            'life': life,
        }, context)
        return True


    def _suppress(self, cr, uid, methods, name, note, context={}):
        for method in methods:
            if method.state == 'open':
                self.pool.get('account.asset.history')._history_line(cr, uid, "suppression", method, name, 0.0, 0.0, False, note, context )
                self.write(cr, uid, [method.id], {
                    'state': 'suppressed'
                })
                method.state='suppressed'
        return True

    def _resume(self, cr, uid, methods, name, note, context={}):
        for method in methods:
            if method.state == 'suppressed':
                self.pool.get('account.asset.history')._history_line(cr, uid, "resuming", method, name, 0.0, 0.0, False, note, context )
                self.write(cr, uid, [method.id], {
                    'state': 'open'
                })
                method.state='open'
        return True


    def _get_next_period(self, cr, uid, context={}):
        period_obj = self.pool.get('account.period')
        periods = period_obj.find(cr, uid, time.strftime('%Y-%m-%d'), context)
        if periods:
            cp = period_obj.browse(cr, uid, periods[0], context)
            return period_obj.next(cr, uid, cp, 1, context)
        else:
            return False

    def _get_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if line.asset_method_id:
                result[line.asset_method_id.id] = True
        return result.keys()


    _name = 'account.asset.method'
    _description = 'Asset method'
    _columns = {
        'name': fields.char('Method name', size=64, select=1, required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'method_type': fields.many2one('account.asset.method.type', 'Method Type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'account_asset_id': fields.many2one('account.account', 'Asset Account', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select account used for cost basis of asset. It will be applied into invoice line when you select this asset in invoice line."),
        'account_expense_id': fields.many2one('account.account', 'Depr. Expense Account', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select account used for depreciation expense (write-off). If you use direct method of depreciation this account should be the same as Asset Account."),
        'account_actif_id': fields.many2one('account.account', 'Depreciation Account', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select account used for depreciation amounts."),
        'account_residual_id': fields.many2one('account.account', 'Sale Residual Account', help = "Select account used for residual when asset is sold. You can change the account before sale operation."),

        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_analytic_id': fields.many2one('account.analytic.journal', 'Analytic Journal', help = "Not implemented yet."),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account', help = "Not implemented yet."),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select period indicating first interval."),
        'method': fields.selection([('linear','Straight-Line'), ('decbalance','Declining-Balance'), ('syd', 'Sum of Years Digits'),  ('uop','Units of Production'), ('progressive','Progressive')], 'Computation Method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'method_progress_factor': fields.float('Progressive Factor', readonly=True, states={'draft':[('readonly',False)]}, help = "Specify the factor of progression in depreciation. Used in Declining-Balance and Progressive method only. When linear depreciation is 20% per year, and you want apply Double-Declining Balance you should choose Declining-Balance method and enter 0,40 (40%) as Progressive factor."),
# TODO You can implement depreciation calculation from fixed date. 
#        'method_time': fields.selection([('interval','Interval'),('date','Start Date')], 'Time Method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
#        'date_start' : fields.date('Start Date',readonly=True, states={'draft':[('readonly',False)]}, help = "Date of depreciation calculation start."),
        'method_delay': fields.integer('Number of Intervals', readonly=True, states={'draft':[('readonly',False)]}, help = "How many intervals this asset is to be calculated in its life. If asset was calculated in other system before specify Intervals Before too."),
        'intervals_before' : fields.integer('Intervals Before', readonly=True, states={'draft':[('readonly',False)]}, help = "Number of intervals calculated before asset is managed in this system. Used with Initial Values wizard. If you start asset in this system keep zero."),
        'method_period': fields.integer('Intervals per Year', readonly=True, states={'draft':[('readonly',False)]}, help = "Specify the number of depreciations to be made in year. This number cannot be less then number of periods in year."),
        'method_salvage': fields.float('Salvage Value', readonly=True, states={'draft':[('readonly',False)]}, help = "Value planned to be residual after full depreciation process"),
        'method_end': fields.date('Ending Date'),
        'date': fields.date('Date Created'),
        'entry_ids': fields.one2many('account.move.line', 'asset_method_id', 'Entries', readonly=True, states={'draft':[('readonly',False)]}),
        'life': fields.float('Life Quantity', readonly=True, states={'draft':[('readonly',False)]}, help = "Quantity of production which make the asset method used up. Used only in Units of Production computation method and cannot be zero in this case."),
        'usage_ids': fields.one2many('account.asset.method.usage', 'asset_method_id', 'Usage'),
        'value_total': fields.function(_amount_total, method=True, digits=(16, int(config['price_accuracy'])), string='Gross Value',
            store={
                'account.asset.method': (lambda self, cr, uid, ids, c={}: ids, ['entry_ids','state'], 10),
                'account.move.line': (_get_line, ['debit','credit','account_id','asset_method_id'], 10),
            },
            multi='all'),
        'value_residual': fields.function(_amount_total, method=True, digits=(16, int(config['price_accuracy'])), string='Residual Value', 
            store={
                'account.asset.method': (lambda self, cr, uid, ids, c={}: ids, ['entry_ids','state'], 10),
                'account.move.line': (_get_line, ['debit','credit','account_id','asset_method_id'], 10),
            },
            multi='all'),
        'state': fields.selection([('draft','Draft'), ('open','Open'), ('suppressed','Suppressed'),('depreciated','Depreciated'), ('close','Closed')], 'Method State', required=True, help = "Open - Ready for calculation.\nSuppressed - Not calculated.\nDepreciated - Depreciation finished but method exists (can be sold or abandoned).\nClosed - Asset method doesn't exist (sold or abandoned)."),

    }

    _defaults = {
#        'type': lambda obj, cr, uid, context: 'direct',
        'state': lambda obj, cr, uid, context: 'draft',
        'method': lambda obj, cr, uid, context: 'linear',
#        'method_time': lambda obj, cr, uid, context: 'interval',
        'method_progress_factor': lambda obj, cr, uid, context: 0.3,
        'method_delay': lambda obj, cr, uid, context: 5,
        'method_period': lambda obj, cr, uid, context: 12,
        'date': lambda obj, cr, uid, context: time.strftime('%Y-%m-%d'),
        'period_id': _get_next_period,
    }

    def unlink(self, cr, uid, ids, context={}):
        for obj in self.browse(cr, uid, ids, context):
            if obj.state != 'draft':
                raise osv.except_osv(_('Error !'), _('You can dalete method only in Draft state !'))
        return super(account_asset_method, self).unlink(cr, uid, ids, context)

    def _check_method(self, cr, uid, ids):
        obj_self = self.browse(cr, uid, ids[0])
        if (12 % obj_self.method_period) == 0:
            return True
        return False

    _constraints = [
        (_check_method, _('Error ! Number of intervals per year must be 1, 2, 3, 4, 6 or 12.'), ['method_period']),
    ]

    def validate(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'open'}, context)
        method = self.browse(cr, uid, ids[0], context)
        self.pool.get('account.asset.asset').write(cr, uid, [method.asset_id.id], {'state':'normal'}, context)
        method.asset_id.state =  'normal'
        return True

    def get_defaults(self, cr, uid, method_type_id, asset_category_id, context={}):
        default_obj = self.pool.get('account.asset.method.defaults')
        if not asset_category_id:
            defaults_id = default_obj.search(cr,uid,[('method_type','=',method_type_id),('asset_category','=',False)])
        else:
            defaults_id = default_obj.search(cr,uid,[('method_type','=',method_type_id),('asset_category','=',asset_category_id)])
            if not defaults_id:
                asset_cat_obj = self.pool.get('account.asset.category')
                parent_cat_id = asset_category_id
                n = 100
                while asset_cat_obj.browse(cr, uid, parent_cat_id,{}).parent_id and not defaults_id and n != 0:
                    parent_cat_id = asset_cat_obj.browse(cr, uid, parent_cat_id,{}).parent_id.id
                    defaults_id = default_obj.search(cr,uid,[('method_type','=',method_type_id),('asset_category','=',parent_cat_id)])
                    n = n - 1
        return defaults_id and default_obj.browse(cr, uid, defaults_id[0],{}) or False

    def onchange_take_defaults(self, cr, uid, ids, method_type_id, name, asset_code, asset_name, asset_category_id, context={}):
        result = {}
        if method_type_id:
            defaults = self.get_defaults(cr, uid, method_type_id, asset_category_id, context)
            if defaults:
                result['account_expense_id'] = defaults.account_expense_id.id
                result['account_actif_id'] = defaults.account_actif_id.id
                result['account_asset_id'] = defaults.account_asset_id.id
                result['account_residual_id'] = defaults.account_residual_id.id
                result['journal_id'] =  defaults.journal_id.id
                result['journal_analytic_id'] = defaults.journal_analytic_id.id
                result['account_analytic_id'] =  defaults.account_analytic_id.id
                result['method'] = defaults.method
                result['method_progress_factor'] =  defaults.method_progress_factor
                result['method_time'] = defaults.method_time
                result['method_delay'] = defaults.method_delay
                result['method_period'] = defaults.method_period
            as_code = asset_code or ""
            as_name = asset_name or ""
            type_code = self.pool.get('account.asset.method.type').browse(cr, uid, method_type_id,{}).code
            result['name'] = as_name + " (" + as_code + ")" + ' - ' + type_code 
        return {'value': result}

# Method is used to post Asset sale, revaluation, abandon and initial values (initial can create 4 lines move)
    def _post_3lines_move(self, cr, uid, method, period, date, acc_third_id, base=0.0, expense=0.0, method_initial=False, reval=False, context={}):
        move_id = self.pool.get('account.move').create(cr, uid, {
            'journal_id': method.journal_id.id,
            'period_id': period.id,
            'date': date,
            'name': '/',                         # GG fix, was 'name': method.name or method.asset_id.name,
            'ref': method.name
        })
        result = [move_id]
        entries =[]
        expense = expense and - expense or False 
        total = base
        if method_initial:
            residual = - total
        elif reval:
            residual = -(base + (expense or 0.0))  # expense is already negative
        else:
            residual =  method.value_residual
        if expense:
            id = self.pool.get('account.move.line').create(cr, uid, {
                'name': method.name or method.asset_id.name,
                'move_id': move_id,
                'account_id': method.account_expense_id.id,
                'debit': expense > 0 and expense or 0.0, 
                'credit': expense < 0 and -expense or 0.0,
                'ref': method.asset_id.code,
                'period_id': period.id,
                'journal_id': method.journal_id.id,
    #            'partner_id': method.asset_id.partner_id.id,
                'date': date,
                'asset_method_id': method.id      
            })
            entries.append((4,id,False),)
            if method_initial:                          # Only for initial values
                id_depr = self.pool.get('account.move.line').create(cr, uid, {
                    'name': method.name or method.asset_id.name,
                    'move_id': move_id,
                    'account_id': method.account_actif_id.id,
                    'debit': expense < 0 and -expense or 0.0, 
                    'credit': expense > 0 and expense or 0.0,
                    'ref': method.asset_id.code,
                    'period_id': period.id,
                    'journal_id': method.journal_id.id,
    #                'partner_id': method.asset_id.partner_id.id,
                    'date': date,
                    'asset_method_id': method.id      
                })
                entries.append((4,id_depr,False),)

        id2 = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': method.account_asset_id.id,
            'debit': total > 0 and total or 0.0, 
            'credit': total < 0 and -total or 0.0, 
            'ref': method.asset_id.code,
            'period_id': period.id,
            'journal_id': method.journal_id.id,
#            'partner_id': method.asset_id.partner_id.id,
            'date': date,
            'asset_method_id': method.id     
        })
        id3 = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': acc_third_id,   #method.account_actif_id.id,
            'debit': residual > 0 and residual or 0.0, 
            'credit': residual < 0 and -residual or 0.0, 
            'ref': method.asset_id.code,
            'period_id': period.id,
            'journal_id': method.journal_id.id,
#            'partner_id': method.asset_id.partner_id.id,
            'date': date,
            'asset_method_id': method.id     
        })
        entries.append([(4, id2, False),(4, id3, False)])
        self.pool.get('account.asset.method').write(cr, uid, [method.id], {
            'entry_ids': entries,
        })
# TODO automatic move posting according to journal setting.
        return result


    def _post_move(self, cr, uid, method, period, date, amount, context={}):
        move_id = self.pool.get('account.move').create(cr, uid, {
            'journal_id': method.journal_id.id,
            'period_id': period.id,
            'date': date,
            'name': '/',                         # GG fix, was 'name': method.name or method.asset_id.name,
            'ref': method.name
        })
        result = [move_id]
        id = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': method.account_expense_id.id,
            'credit': amount>0 and amount or 0.0,  
            'debit': amount<0 and -amount or 0.0, 
            'ref': method.asset_id.code,
            'period_id': period.id,
            'journal_id': method.journal_id.id,
#            'partner_id': method.asset_id.partner_id.id,
            'date': date,
            'asset_method_id': method.id      
        })
        id2 = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': method.account_actif_id.id,
            'debit': amount >0 and amount or 0.0, 
            'credit': amount <0 and -amount or 0.0, 
            'ref': method.asset_id.code,
            'period_id': period.id,
            'journal_id': method.journal_id.id,
#            'partner_id': method.asset_id.partner_id.id,
            'date': date,
            'asset_method_id': method.id     
        })
        self.pool.get('account.asset.method').write(cr, uid, [method.id], {
            'entry_ids': [(4, id2, False),(4,id,False)]
        })
# TODO automatic move posting according to journal setting.
        return result

    def _compute_move(self, cr, uid, method, period, date, usage, last_move_line, context={}):
        result = []
        gross = method.value_total - method.method_salvage
        to_writeoff = method.value_residual - method.method_salvage 
        if usage:                # Units of Production method
            amount = gross * usage / method.life
        else:
            depr_entries_made = method.intervals_before
            for line in method.entry_ids:
                if (line.account_id == method.account_actif_id) and (line.period_id.date_start >= method.period_id.date_start):
                    depr_entries_made += 1      # count depreciation already made
            intervals = method.method_delay - depr_entries_made
            if intervals == 1:
                amount = to_writeoff
            else:
                if method.method == 'linear':
                    amount = to_writeoff / intervals
                elif method.method == 'progressive':    # probably obsolete method
                    amount = to_writeoff * method.method_progress_factor
                elif method.method == 'decbalance':
                    period_end = mx.DateTime.strptime(period.date_stop, '%Y-%m-%d')
                    if depr_entries_made == 0:                              # First year
                        amount = to_writeoff * method.method_progress_factor / method.method_period 
                    elif (12 / period_end.month) == method.method_period:                      # First interval in calendar year
                        amount = to_writeoff * method.method_progress_factor / method.method_period
                        if amount < (gross / method.method_delay):   # In declining-balance when amount less than amount for linear it switches to linear
                            amount = gross / method.method_delay
                    else:                                            # In other cases repeat last entry
                        amount = last_move_line.debit
                elif method.method == 'syd':                         # Sum of Year Digits method
                    years = method.method_delay / method.method_period
                    syd = years * (years + 1) / 2
                    year = years - math.floor(depr_entries_made / method.method_period)
                    if (depr_entries_made % method.method_period) == 0:                          # First interval in 12 month cycle
                        amount = gross * year / syd / method.method_period 
                    else:                                              # In other cases repeat last entry
                        amount = last_move_line.debit
        if amount > to_writeoff:
            amount = to_writeoff

        result = self._post_move(cr, uid, method, period, date, amount, context)

        if (to_writeoff == amount): 
            self.pool.get('account.asset.method')._finish_depreciation(cr, uid, method, context)
        return result

    def _compute_last_calculated(self, cr, uid, method, period, context={}):
        cr.execute("SELECT m.id, m.period_id \
                        FROM account_move_line AS m \
                            WHERE m.asset_method_id = %s AND m.account_id = %s \
                            ORDER BY m.id DESC", (method.id, method.account_actif_id.id,))
        pid = cr.fetchone()
        if pid:
            periods_obj = self.pool.get('account.period')
            last_period = periods_obj.browse(cr, uid, pid[1], context)
            if last_period.date_start < period.date_start:
                ml_obj = self.pool.get('account.move.line')
                last_move_line = ml_obj.browse(cr, uid, pid[0], context)
                return last_move_line, True                # last move line exists and do compute
            else:
                return False, False        # last move line doesn't exists and don't compute
        return False, True            # last move line doesn't exists but do compute

    def _compute_entries(self, cr, uid, method, period, date, context={}):
        result = []
        if (method.state=='open') and (period.date_start >= method.period_id.date_start):
            usage = False
            period_ok = False
            last_move_line, compute_period = self._compute_last_calculated(cr, uid, method, period, context)
            if compute_period:          # it was no calculation for period yet
                if method.method == 'uop':
                    usage_obj = self.pool.get('account.asset.method.usage')
                    usage_ids = usage_obj.search(cr, uid, [('period_id','=',period.id),('asset_method_id','=',method.id)])
                    usage = usage_ids and usage_obj.browse(cr, uid, usage_ids[0], context).usage or False
                else:
                    period_ok = ((mx.DateTime.strptime(period.date_stop, '%Y-%m-%d').month % (12 / method.method_period)) == 0)
                if (period_ok or usage):
                    result += self._compute_move(cr, uid, method, period, date, usage, last_move_line, context)
        return result

    def _check_date(self, cr, uid, period_id, date, context={}):
        period_obj = self.pool.get('account.period')
        period = period_obj.browse(cr, uid, period_id, context)
        if (period.date_start > date) or (period.date_stop < date):
            raise osv.except_osv(_('Error !'), _('Date must be in the period !'))
        if period.state == 'done':
            raise osv.except_osv(_('Error !'), _('Cannot post in closed period !'))
        return period

account_asset_method()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Asset Depr. Method', help = "Assign the asset as depreciation method if move line concerns the asset."),
    }
account_move_line()

class account_asset_history(osv.osv):
    _name = 'account.asset.history'
    _description = 'Asset history'

    _columns = {
        'name': fields.char('History name', size=64, select=1),
        'type': fields.selection([
                ('change','Settings Change'), 
                ('purchase','Purchase'),       # Crated after purchase for any method
                ('refund','Purchase Refund'),  # Crated after purchase refund for any method
                ('reval', 'Revaluation'),      # Crated after purchase for any method
                ('initial', 'Initial Value'),  
                ('sale','Sale'), 
                ('closing','Closing'),       # not used already
                ('abandon','Abandonment'), 
                ('suppression','Depr. Suppression'), 
                ('resuming','Depr. Resuming'),
                ('summary','Summary'),          # Created after Summary on demand. Creates Summary of all methods (not implemented yet)
                ('transfer','Transfer')],       # Creted after changing of localisation 
            'Entry Type', required=True, readonly=True),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'date': fields.date('Date', required=True),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True),
        'asset_method_id': fields.many2one('account.asset.method', 'Method', ),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'change_total': fields.float('Total Change', digits=(16, int(config['price_accuracy']))),
        'change_expense': fields.float('Expense Change', digits=(16, int(config['price_accuracy']))),
        'method_end': fields.date('Ending Date'),    # not used
        'note': fields.text('Note'),
    }
    _defaults = {
        'date': lambda *args: time.strftime('%Y-%m-%d'),
        'user_id': lambda self,cr, uid,ctx: uid,
    }

    def _history_line(self, cr, uid, type, method, name, total, expense, invoice, note, context={} ):
        if type in ["purchase","initial"]:
            note = _("Parameters set to:") + \
                    _('\n   Number of Intervals: ')+ str(method.method_delay) + \
                    _('\n   Intervals per Year: ')+ str(method.method_period) + \
                    _('\n   Progressive Factor: ') + str(method.method_progress_factor) + \
                    _('\n   Salvage Value: ') + str(method.method_salvage or 0.0)+ \
                    _('\n   Life Quantity: ') + str(method.life or 0.0)+ \
                    _('\n   Intervals Before: ') + str(method.intervals_before or 0.0)+ \
                    "\n" + str(note or "")

        self.pool.get('account.asset.history').create(cr, uid, {
             'type': type,
             'asset_method_id': method.id,
             'asset_id' : method.asset_id.id,
             'name': name,
             'partner_id': invoice and invoice.partner_id.id,
             'invoice_id': invoice and invoice.id,
             'change_total': total,
             'change_expense': expense,
#             'method_total': method.value_total,
#             'method_residual': method.value_residual,
#             'asset_total': method.asset_id.amount_total,
#             'asset_residual': method.asset_id.amount_residual,
             'note': str(note or ""),
        })


account_asset_history()

class account_asset_method_usage(osv.osv):
    _name = 'account.asset.method.usage'
    _description = 'Asset Method Usage'

    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False

    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Method',required=True,),
        'period_id': fields.many2one('account.period', 'Period', required=True, help = "Select period which usage concerns."),
        'usage': fields.float('Usage', help = "Specify usage quantity in selected period."),
    }

    _defaults = {
        'period_id': _get_period,
    }
account_asset_method_usage()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


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
import mx.DateTime
#from mx.DateTime import RelativeDateTime, now, DateTime, localtime

class account_asset_category(osv.osv):
    _name = 'account.asset.category'
    _description = 'Asset category'
    _columns = {
        'code': fields.char('Asset Category Code', size=16, required=True, select=1),
        'name': fields.char('Asset category', size=64, required=True, select=1),
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
        (_check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
account_asset_category()

class account_asset_asset(osv.osv):
    _name = 'account.asset.asset'
    _description = 'Asset'

#   def _balance(self, cr, uid, ids, field_name, arg, context={}):
#       acc_set = ",".join(map(str, ids))
#       query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
#       cr.execute(("SELECT a.id, COALESCE(SUM((l.debit-l.credit)),0) FROM account_asset_asset a LEFT JOIN account_move_line l ON (a.id=l.asset_account_id) WHERE a.id IN (%s) and "+query+" GROUP BY a.id") % (acc_set,))
#       res = {}
#       for account_id, sum in cr.fetchall():
#           res[account_id] = round(sum,2)
#       for id in ids:
#           res[id] = round(res.get(id,0.0), 2)
#       return res
    '''
    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False
    '''

    def validate(self, cr, uid, ids, context={}):
        for asset in self.browse(cr, uid, ids, context):
            for prop in asset.method_ids:
                if prop.state=='draft':
                    self.pool.get('account.asset.method').write(cr, uid, [prop.id], {'state':'open'}, context)
        return self.write(cr, uid, ids, {
            'state':'normal'
        }, context)

    '''
    def _amount_total(self, cr, uid, ids, name, args, context={}):
        id_set=",".join(map(str,ids))
        cr.execute("""SELECT l.asset_id, abs(SUM(l.debit-l.credit)) AS amount FROM 
                account_move_line l
            WHERE l.asset_id IN ("""+id_set+") GROUP BY l.asset_id ")
        res=dict(cr.fetchall())
        for id in ids:
            res.setdefault(id, 0.0)
        return res
    '''

    _columns = {
        'name': fields.char('Asset', size=64, required=True, select=1),
        'code': fields.char('Asset code', size=16, select=1),
        'note': fields.text('Note'),
        'category_id': fields.many2one('account.asset.category', 'Asset category', change_default=True),
        'localisation': fields.char('Localisation', size=32, select=2),
        'sequence': fields.integer('Sequence'),
#        'parent_id': fields.many2one('account.asset.asset', 'Parent asset'),
#        'child_ids': fields.one2many('account.asset.asset', 'parent_id', 'Childs asset'),
        'date': fields.date('Date', required=True),
        'state': fields.selection([('view','View'),('draft','Draft'),('normal','Normal'),('close','Close')], 'Asset State', required=True),
        'active': fields.boolean('Active', select=2),
        'partner_id': fields.many2one('res.partner', 'Partner'),
#        'entry_ids': fields.one2many('account.move.line', 'asset_id', 'Entries', readonly=True, states={'draft':[('readonly',False)]}),
        'method_ids': fields.one2many('account.asset.method', 'asset_id', 'Asset method name', readonly=True, states={'draft':[('readonly',False)]}),
#        'value_total': fields.function(_amount_total, method=True, digits=(16,2),string='Total value'),
#        'value_salvage': fields.float('Total Salvage', readonly=True, states={'draft':[('readonly',False)]}, help = "Value planned to be residual after full depreciation process")
    }
    _defaults = {
        'code': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'account.asset.code'),
        'date': lambda obj, cr, uid, context: time.strftime('%Y-%m-%d'),
        'active': lambda obj, cr, uid, context: True,
        'state': lambda obj, cr, uid, context: 'draft',
#        'period_id': _get_period,
    }
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
        'method_type': fields.many2one('account.asset.method.type', 'Method Type', required = True, help ="Select method type for this set of defaults."),
        'account_asset_id': fields.many2one('account.account', 'Asset account', help = "Select account used as cost basis of asset. It will be applied into invoice line when you select this asset in invoice line."),
        'account_expense_id': fields.many2one('account.account', 'Depr. Expense account', help = "Select account used as depreciation expense (write-off). If you use direct method of depreciation this account should be the same as Asset Account."),
        'account_actif_id': fields.many2one('account.account', 'Depreciation account',  help = "Select account used as depreciation amount."),
        'journal_id': fields.many2one('account.journal', 'Journal', ),
        'journal_analytic_id': fields.many2one('account.analytic.journal', 'Analytic journal'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic account'),
        'method': fields.selection([('linear','Linear'),('progressive','Progressive'), ('decbalance','Declining-Balance')], 'Computation method'),
        'method_progress_factor': fields.float('Progressive factor', help = "Specify the factor of progression in depreciation. It is not used in Linear method. When linear depreciation is 20% per year, and you want apply Double-Declining Balance you should choose Declining-Balance method and enter 0,40 (40%) as Progressive factor."),
        'method_time': fields.selection([('interval','Interval'),('endofyear','End of Year')], 'Time method'),
        'method_delay': fields.integer('Number of intervals'),
        'method_period': fields.integer('Periods per interval'),

    }

    _defaults = {
        'method': lambda obj, cr, uid, context: 'linear',
        'method_time': lambda obj, cr, uid, context: 'interval',
        'method_progress_factor': lambda obj, cr, uid, context: 0.3,
        'method_delay': lambda obj, cr, uid, context: 5,
        'method_period': lambda obj, cr, uid, context: 12,
    }

account_asset_method_defaults()


class account_asset_method(osv.osv):              # Asset method = Asset Method
    def _amount_total(self, cr, uid, ids, name, args, context={}):

        # FIXME sql query below "sometimes" doesn't work - returns 0.0 - cannot guess why
        # Usualy stop to work after module updating.
#        res = {}
#        for val in self.browse(cr, uid, ids, context=context):
        if not ids:
            return {}
        id_set=",".join(map(str,ids))
        res = {}
        for id in ids: #
            res[id] = {'value_total': 0.0 , 'value_residual': 0.0}
        cr.execute("SELECT p.id, SUM(l.debit) AS total, SUM(l.credit) AS residual \
                            FROM account_asset_method p \
                            LEFT JOIN account_move_line l \
                                ON (p.id=l.asset_method_id) \
                            WHERE p.id IN ("+id_set+") AND p.account_asset_id = l.account_id \
                            GROUP BY p.id ")
#        res=cr.fetchall()
        for id, dt1, dt2 in cr.fetchall():
            res[id]['value_total'] = dt1
            res[id]['value_residual'] = dt2
#            for id in ids:
#                res.setdefault(id, (0.0, 0.0))
#            res['residual'].setdefault(id, 0.0)
        return res
    '''
    def _amount_residual(self, cr, uid, ids, name, args, context={}):
        id_set=",".join(map(str,ids))
        cr.execute("""SELECT r.asset_method_id,SUM(l.credit) AS amount
                        FROM account_asset_method p
                        LEFT JOIN account_move_line l 
                            ON (p.asset_id = l.asset_id)
                        WHERE p.id IN ("""+id_set+") \
                        AND  p.account_asset_id = l.account_id GROUP BY p.asset_id ")
        res=dict(cr.fetchall())
        for prop in self.browse(cr, uid, ids, context):
            res[prop.id] = prop.value_total - res.get(prop.id, 0.0)/2  # GG fix - '/2'
        for id in ids:
            res.setdefault(id, 0.0)
        return res
    '''

    def _close(self, cr, uid, method, context={}):
        if method.state<>'close':
            self.pool.get('account.asset.method').write(cr, uid, [method.id], {
                'state': 'close'
            })
            method.state='close'
        ok = method.asset_id.state=='open'
        for prop in method.asset_id.method_ids:
            ok = ok and prop.state=='close'
        if ok:
            self.pool.get('account.asset.asset').write(cr, uid, [method.asset_id.id], {
                'state': 'close'
            }, context)
        return True

    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False

    _name = 'account.asset.method'
    _description = 'Asset method'
    _columns = {
        'name': fields.char('Method name', size=64, select=1),
        'method_type': fields.many2one('account.asset.method.type', 'Method Type'),
#        'type': fields.selection([('direct','Direct'),('indirect','Indirect')], 'Depr. method type', select=2, required=True),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'account_asset_id': fields.many2one('account.account', 'Asset account', required=True, help = "Select account used as cost basis of asset. It will be applied into invoice line when you select this asset in invoice line."),
        'account_expense_id': fields.many2one('account.account', 'Depr. Expense account', required=True, help = "Select account used as depreciation expense (write-off). If you use direct method of depreciation this account should be the same as Asset Account."),
        'account_actif_id': fields.many2one('account.account', 'Depreciation account', required=True, help = "Select account used as depreciation amount."),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True),
        'journal_analytic_id': fields.many2one('account.analytic.journal', 'Analytic journal'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic account'),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select period when depreciation should be started"),
        'method': fields.selection([('linear','Straight-Line'), ('decbalance','Declining-Balance'), ('syd', 'Sum of Years Digits'),  ('uop','Units of Production'), ('progressive','Progressive')], 'Computation method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'method_progress_factor': fields.float('Progressive factor', readonly=True, states={'draft':[('readonly',False)]}, help = "Specify the factor of progression in depreciation. It is not used in Linear method. When linear depreciation is 20% per year, and you want apply Double-Declining Balance you should choose Declining-Balance method and enter 0,40 (40%) as Progressive factor."),
        'method_time': fields.selection([('interval','Interval'),('endofyear','End of Year')], 'Time method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'method_delay': fields.integer('Number of intervals', readonly=True, states={'draft':[('readonly',False)]}),
        'method_period': fields.integer('Periods per interval', readonly=True, states={'draft':[('readonly',False)]}),
        'method_salvage': fields.float('Salvage Value', readonly=True, states={'draft':[('readonly',False)]}, help = "Value planned to be residual after full depreciation process"),
        'method_end': fields.date('Ending date'),

        'date': fields.date('Date created'),
        'entry_ids': fields.one2many('account.move.line', 'asset_method_id', 'Entries', readonly=True, states={'draft':[('readonly',False)]}),

#        'entry_asset_ids': fields.many2many('account.move.line', 'account_move_asset_entry_rel', 'asset_method_id', 'move_id', 'Asset Entries'),
#        'board_ids': fields.one2many('account.asset.board', 'asset_id', 'Asset board'),

        'value_total': fields.function(_amount_total, method=True, digits=(16,2),string='Gross value', multi = "total"),
        'value_residual': fields.function(_amount_total, method=True, digits=(16,2), string='Residual value', multi = "residual"),
        'state': fields.selection([('draft','Draft'), ('open','Open'), ('close','Close')], 'Method State', required=True),
        'history_ids': fields.one2many('account.asset.method.history', 'asset_method_id', 'History', readonly=True)
    }
    _defaults = {
#        'type': lambda obj, cr, uid, context: 'direct',
        'state': lambda obj, cr, uid, context: 'draft',
        'method': lambda obj, cr, uid, context: 'linear',
        'method_time': lambda obj, cr, uid, context: 'interval',
        'method_progress_factor': lambda obj, cr, uid, context: 0.3,
        'method_delay': lambda obj, cr, uid, context: 5,
        'method_period': lambda obj, cr, uid, context: 12,
        'date': lambda obj, cr, uid, context: time.strftime('%Y-%m-%d'),
        'period_id': _get_period,
    }

    def validate(self, cr, uid, ids, context={}):
        for prop in self.browse(cr, uid, ids, context):
            if prop.asset_id.state=='draft':
                self.pool.get('account.asset.asset').write(cr, uid, [prop.asset_id.id], {'state':'normal'}, context)
        return self.write(cr, uid, ids, {
            'state':'open'
        }, context)

    def onchange_take_defaults(self, cr, uid, ids, method_type, name, asset_code, asset_name, asset_category_id, context={}):
#        if not asset_code:
#            raise osv.except_osv('Error !', 'You must enterIDS %s'%ids)  
        result = {}
        if method_type:
            default_obj = self.pool.get('account.asset.method.defaults')
            if not asset_category_id:
                defaults_id = default_obj.search(cr,uid,[('method_type','=',method_type),('asset_category','=',False)])
            else:
                defaults_id = default_obj.search(cr,uid,[('method_type','=',method_type),('asset_category','=',asset_category_id)])
                if not defaults_id:
                    asset_cat_obj = self.pool.get('account.asset.category')
                    parent_cat_id = asset_category_id
                    n = 10
                    while not defaults_id or n == 0:
                        parent_cat_id = asset_cat_obj.browse(cr, uid, parent_cat_id,{}).parent_id.id
                        defaults_id = default_obj.search(cr,uid,[('method_type','=',method_type),('asset_category','=',parent_cat_id)])
                        n = n - 1
            if defaults_id:
                defaults = default_obj.browse(cr, uid, defaults_id[0],{})
                result['account_expense_id'] = defaults.account_expense_id.id
                result['account_actif_id'] = defaults.account_actif_id.id
                result['account_asset_id'] = defaults.account_asset_id.id
                result['journal_id'] =  defaults.journal_id.id
                result['journal_analytic_id'] = defaults.journal_analytic_id.id
                result['account_analytic_id'] =  defaults.account_analytic_id.id
                result['method'] = defaults.method
                result['method_progress_factor'] =  defaults.method_progress_factor
                result['method_time'] = defaults.method_time
                result['method_delay'] = defaults.method_delay
                result['method_period'] = defaults.method_period
#            if not name:
#                prop_obj = self.pool.get('account.asset.method').browse(cr, uid, ids,{})
            as_code = asset_code or ""
            as_name = asset_name or ""
            type_code = self.pool.get('account.asset.method.type').browse(cr, uid, method_type,{}).code
            result['name'] = type_code + '-' + as_name +  " ("  + as_code + ")"
        return {'value': result}

    def _compute_period(self, cr, uid, method, context={}):
        if (len(method.entry_ids or [])/2)>=method.method_delay:
            return False
        if len(method.entry_ids):
                                                                                            # GG fix begin
            cr.execute("SELECT m.id, m.period_id \
                        FROM account_move_line AS m " +
#                            LEFT JOIN account_move_asset_entry_rel AS r \
#                            ON m.id = r.move_id \

                                "LEFT JOIN account_asset_method AS p \
                                ON p.id = r.asset_method_id \
                            WHERE p.id = %s \
                            ORDER BY m.id DESC", (method,))
            pid = cr.fetchone()[1]
            periods_obj = self.pool.get('account.period')
            cp = periods_obj.browse(cr, uid, pid, context)
            cpid = periods_obj.next(cr, uid, cp, method.method_period, context)
            if not cpid:                                                                   
                raise osv.except_osv(_('Error !'), _('Next periods not defined yet !'))     
            current_period = periods_obj.browse(cr, uid, cpid, context)                              # GG fix end
        else:
            current_period = method.period_id
        return current_period

    def _compute_move(self, cr, uid, method, period, context={}):
        result = []
        total = 0.0
        depr_entries_made = 0
        for move in method.entry_ids:
            if move.account_id == method.account_asset_id:
                total += move.debit    #-move.credit
            if move.account_id == method.account_expense_id:
                total -= move.credit
                depr_entries_made += 1 
        total -= method.value_salvage
        gross = total                                       # GG fix needed for declining-balance
#        for move in method.entry_asset_ids:
#            if move.account_id == method.account_expense_id:
#                total += move.debit-move.credit
#        entries_made = (len(method.entry_asset_ids)/2)   # GG fix needed for declining-balance
        periods = method.method_delay - entries_made     # GG fix
        if periods==1:
            amount = total
        else:
            if method.method == 'linear':
                amount = total / periods
            elif method.method == 'progressive':                          # GG fix begin 
                amount = total * method.method_progress_factor
            elif method.method == 'decbalance':
                period_begin = mx.DateTime.strptime(period.date_start, '%Y-%m-%d')
                period_end = mx.DateTime.strptime(period.date_stop, '%Y-%m-%d')
                period_duration = period_end.month - period_begin.month + 1 
                intervals_per_year = 12 / period_duration / method.method_period
                if entries_made == 0:                              # First year
                    remaining_intervals = 1 + abs((12 - period_end.month) / period_duration / method.method_period)
                    amount = (total * method.method_progress_factor * remaining_intervals / intervals_per_year) / remaining_intervals
                elif (12 / period_end.month) >= intervals_per_year:                      # Beginning of the year
                    amount = total * method.method_progress_factor / intervals_per_year
                    if amount < (gross / method.method_delay):   # In declining-balance when amount less than amount for linear it switches to linear
                        amount = gross / method.method_delay
                else:                                              # In other cases repeat last entry
                    cr.execute("SELECT m.id, m.debit \
                                FROM account_move_line AS m \
                                    LEFT JOIN account_move_asset_entry_rel AS r \
                                    ON m.id = r.move_id \
                                        LEFT JOIN account_asset_method AS p \
                                        ON p.asset_id = r.asset_method_id \
                                    WHERE p.asset_id = %s \
                                    ORDER BY m.id DESC", (method.asset_id.id,))
                    amount = cr.fetchone()[1]
                if total < amount:
                    amount = total
                                                                             # GG fix end
        move_id = self.pool.get('account.move').create(cr, uid, {
            'journal_id': method.journal_id.id,
            'period_id': period.id,
            'name': '/',                         # GG fix, was 'name': method.name or method.asset_id.name,
            'ref': method.asset_id.code
        })
        result = [move_id]
        id = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': method.account_expense_id.id,
            'credit': amount>0 and amount or 0.0,       # GG fix
            'debit': amount<0 and -amount or 0.0,       # GG fix
            'ref': method.asset_id.code,
            'period_id': period.id,
            'journal_id': method.journal_id.id,
            'partner_id': method.asset_id.partner_id.id,
            'date': time.strftime('%Y-%m-%d'),
    #            'asset_id': method.asset_id.id      # Probably should be added but some other querries should be changed
        })
        id2 = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': method.account_actif_id.id,
            'debit': amount>0 and amount or 0.0,            # GG fix
            'credit': amount<0 and -amount or 0.0,          # GG fix
            'ref': method.asset_id.code,
            'period_id': period.id,
            'journal_id': method.journal_id.id,
            'partner_id': method.asset_id.partner_id.id,
            'date': time.strftime('%Y-%m-%d'),
    #            'asset_id': method.asset_id.id      # Probably should be added but some other querries should be changed
        })
        self.pool.get('account.asset.method').write(cr, uid, [method.id], {
            'entry_asset_ids': [(4, id2, False),(4,id,False)]
        })
        if (method.method_delay - (len(method.entry_asset_ids)/2)<=1) or (total == amount):  # GG fix for declining-balance
            self.pool.get('account.asset.method')._close(cr, uid, method, context)
            return result
        return result

    def _compute_entries(self, cr, uid, method, period_id, context={}):
        result = []
        date_start = self.pool.get('account.period').browse(cr, uid, period_id, context).date_start
        if method.state=='open':
            period = self._compute_period(cr, uid, method, context)
            if period and (period.date_start<=date_start):
                result += self._compute_move(cr, uid, method, period, context)
        return result


account_asset_method()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Asset Depr. Method'),
    }
account_move_line()

class account_asset_method_history(osv.osv):
    _name = 'account.asset.method.history'
    _description = 'Asset history'
    _columns = {
        'name': fields.char('History name', size=64, select=1),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'date': fields.date('Date', required=True),
        'asset_method_id': fields.many2one('account.asset.method', 'Method', required=True),
        'method_delay': fields.integer('Number of interval'),
        'method_period': fields.integer('Period per interval'),
        'method_end': fields.date('Ending date'),
        'note': fields.text('Note'),
    }
    _defaults = {
        'date': lambda *args: time.strftime('%Y-%m-%d'),
        'user_id': lambda self,cr, uid,ctx: uid
    }
account_asset_method_history()

'''
class account_asset_board(osv.osv):
    _name = 'account.asset.board'
    _description = 'Asset board'
    _columns = {
        'name': fields.char('Asset name', size=64, required=True, select=1),
        'asset_id': fields.many2one('account.asset.method', 'Asset', required=True, select=1),
        'value_gross': fields.float('Gross value', required=True, select=1),
        'value_asset': fields.float('Asset Value', required=True, select=1),
        'value_asset_cumul': fields.float('Cumul. value', required=True, select=1),
        'value_net': fields.float('Net value', required=True, select=1),
    }
    _auto = False
    def init(self, cr):
        cr.execute("""
            create or replace view account_asset_board as (
                select
                    min(l.id) as id,
                    min(l.id) as asset_id,
                    0.0 as value_gross,
                    0.0 as value_asset,
                    0.0 as value_asset_cumul,
                    0.0 as value_net
                from
                    account_move_line l
                where
                    l.state <> 'draft' and
                    l.asset_id=3
            )""")
account_asset_board()
'''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


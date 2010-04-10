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
        'code': fields.char('Asset Code', size=16, select=1),
        'note': fields.text('Note'),
        'category_id': fields.many2one('account.asset.category', 'Asset Category', change_default=True),
        'localisation': fields.char('Localisation', size=32, select=2),
        'sequence': fields.integer('Sequence'),
#        'parent_id': fields.many2one('account.asset.asset', 'Parent asset'),
#        'child_ids': fields.one2many('account.asset.asset', 'parent_id', 'Childs asset'),
        'date': fields.date('Date', required=True),
        'state': fields.selection([('view','View'),('draft','Draft'),('normal','Normal'),('close','Close')], 'Asset State', required=True),
        'active': fields.boolean('Active', select=2),
        'partner_id': fields.many2one('res.partner', 'Partner'),
#        'entry_ids': fields.one2many('account.move.line', 'asset_id', 'Entries', readonly=True, states={'draft':[('readonly',False)]}),
        'method_ids': fields.one2many('account.asset.method', 'asset_id', 'Asset Method Name', readonly=False, states={'close':[('readonly',True)]}),
#        'value_total': fields.function(_amount_total, method=True, digits=(16,2),string='Total value'),
#        'value_salvage': fields.float('Total Salvage', readonly=True, states={'draft':[('readonly',False)]}, help = "Value planned to be residual after full depreciation process")
        'history_ids': fields.one2many('account.asset.history', 'asset_id', 'History', readonly=True)
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
        'account_asset_id': fields.many2one('account.account', 'Asset Account', help = "Select account used as cost basis of asset. It will be applied into invoice line when you select this asset in invoice line."),
        'account_expense_id': fields.many2one('account.account', 'Depr. Expense Account', help = "Select account used as depreciation expense (write-off). If you use direct method of depreciation this account should be the same as Asset Account."),
        'account_actif_id': fields.many2one('account.account', 'Depreciation Account',  help = "Select account used as depreciation amount."),
        'journal_id': fields.many2one('account.journal', 'Journal', ),
        'journal_analytic_id': fields.many2one('account.analytic.journal', 'Analytic Journal'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'method': fields.selection([('linear','Linear'),('progressive','Progressive'), ('decbalance','Declining-Balance')], 'Computation Method'),
        'method_progress_factor': fields.float('Progressive factor', help = "Specify the factor of progression in depreciation. It is not used in Linear method. When linear depreciation is 20% per year, and you want apply Double-Declining Balance you should choose Declining-Balance method and enter 0,40 (40%) as Progressive factor."),
        'method_time': fields.selection([('interval','Interval'),('endofyear','End of Year')], 'Time Method'),
        'method_delay': fields.integer('Number of Intervals'),
        'method_period': fields.integer('Periods per Interval'),

    }

    _defaults = {
        'method': lambda obj, cr, uid, context: 'linear',
        'method_time': lambda obj, cr, uid, context: 'interval',
        'method_progress_factor': lambda obj, cr, uid, context: 0.3,
        'method_delay': lambda obj, cr, uid, context: 5,
        'method_period': lambda obj, cr, uid, context: 1,
    }

account_asset_method_defaults()


class account_asset_method(osv.osv):              # Asset method = Asset Method
    def _amount_total(self, cr, uid, ids, name, args, context={}):

        if not ids:
            return {}
        id_set=",".join(map(str,ids))
        res = {}
        for id in ids: #
            res[id] = {'value_total': 0.0 , 'value_residual': 0.0}
        cr.execute("SELECT p.id, SUM(l.debit-l.credit) AS total \
                            FROM account_asset_method p \
                            LEFT JOIN account_move_line l \
                                ON (p.id=l.asset_method_id) \
                            WHERE p.id IN ("+id_set+") AND p.account_asset_id = l.account_id \
                            GROUP BY p.id ")
        totals = cr.fetchall()
        cr.execute("SELECT p.id, SUM(l.credit) AS writeoff \
                            FROM account_asset_method p \
                            LEFT JOIN account_move_line l \
                                ON (p.id=l.asset_method_id) \
                            WHERE p.id IN ("+id_set+") AND p.account_expense_id = l.account_id \
                            GROUP BY p.id ")
        write_offs = cr.fetchall()
 
        for id, dt1 in totals:
            res[id]['value_total'] = dt1
            res[id]['value_residual'] = dt1
        for id, dt2 in write_offs:
            res[id]['value_residual'] = res[id]['value_total'] - dt2
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
                        AND  p.account_expense_id = l.account_id GROUP BY p.id ")
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
        ok = method.asset_id.state=='normal'
        for prop in method.asset_id.method_ids:
            ok = ok and prop.state=='close'
        if ok:
            self.pool.get('account.asset.asset').write(cr, uid, [method.asset_id.id], {
                'state': 'close'
            }, context)
        return True

    def _get_next_period(self, cr, uid, context={}):
        period_obj = self.pool.get('account.period')
        periods = period_obj.find(cr, uid)
        if periods:
            cp = period_obj.browse(cr, uid, periods[0], context)
            return period_obj.next(cr, uid, cp, 1, context)
        else:
            return False

    _name = 'account.asset.method'
    _description = 'Asset method'
    _columns = {
        'name': fields.char('Method name', size=64, select=1),
        'method_type': fields.many2one('account.asset.method.type', 'Method Type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
#        'type': fields.selection([('direct','Direct'),('indirect','Indirect')], 'Depr. method type', select=2, required=True),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'account_asset_id': fields.many2one('account.account', 'Asset Account', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select account used as cost basis of asset. It will be applied into invoice line when you select this asset in invoice line."),
        'account_expense_id': fields.many2one('account.account', 'Depr. Expense Account', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select account used as depreciation expense (write-off). If you use direct method of depreciation this account should be the same as Asset Account."),
        'account_actif_id': fields.many2one('account.account', 'Depreciation Account', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select account used as depreciation amount."),
        'account_residual_id': fields.many2one('account.account', 'Residual Account', help = "Select account used as residual for method when asset is sold or liquidated. You can change the account before operation."),

        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'journal_analytic_id': fields.many2one('account.analytic.journal', 'Analytic Journal',),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account',),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}, help = "Select last period of starting Interval."),
        'method': fields.selection([('linear','Straight-Line'), ('decbalance','Declining-Balance'), ('syd', 'Sum of Years Digits'),  ('uop','Units of Production'), ('progressive','Progressive')], 'Computation Method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'method_progress_factor': fields.float('Progressive Factor', readonly=True, states={'draft':[('readonly',False)]}, help = "Specify the factor of progression in depreciation. It is not used in Linear method. When linear depreciation is 20% per year, and you want apply Double-Declining Balance you should choose Declining-Balance method and enter 0,40 (40%) as Progressive factor."),
        'method_time': fields.selection([('interval','Interval'),('endofyear','End of Year')], 'Time Method', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'method_delay': fields.integer('Number of Intervals', readonly=True, states={'draft':[('readonly',False)]}),
        'method_period': fields.integer('Intervals per Year', readonly=True, states={'draft':[('readonly',False)]}, help = "Specify the number of depreciations to be made in year. This number cannot be less then number of periods in year."),
        'method_salvage': fields.float('Salvage Value', readonly=True, states={'draft':[('readonly',False)]}, help = "Value planned to be residual after full depreciation process"),
        'method_end': fields.date('Ending Date'),

        'date': fields.date('Date Created'),
        'entry_ids': fields.one2many('account.move.line', 'asset_method_id', 'Entries', readonly=True, states={'draft':[('readonly',False)]}),
        'life': fields.float('Life Quantity', readonly=True, states={'draft':[('readonly',False)]}, help = "Quantity of production which make the asset method used up. This is used in Units Of Production computation method."),
        'usage_ids': fields.one2many('account.asset.method.usage', 'asset_method_id', 'Usage'),

#        'entry_asset_ids': fields.many2many('account.move.line', 'account_move_asset_entry_rel', 'asset_method_id', 'move_id', 'Asset Entries'),
#        'board_ids': fields.one2many('account.asset.board', 'asset_id', 'Asset board'),

        'value_total': fields.function(_amount_total, method=True, digits=(16,2),string='Gross Value', multi = "total"),
        'value_residual': fields.function(_amount_total, method=True, digits=(16,2), string='Residual Value', multi = "residual"),
        'state': fields.selection([('draft','Draft'), ('open','Open'), ('close','Close')], 'Method State', required=True),

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
        'period_id': _get_next_period,
    }

    def _check_period(self, cr, uid, ids):
        obj_self = self.browse(cr, uid, ids[0])
        if (mx.DateTime.strptime(obj_self.period_id.date_stop, '%Y-%m-%d').month % (12 / obj_self.method_period)) == 0:
            return True
        return False



    _constraints = [
        (_check_period, 'Error ! Period must be as last in interval.', ['period_id'])
    ]

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
                    n = 100
                    while asset_cat_obj.browse(cr, uid, parent_cat_id,{}).parent_id and not defaults_id and n != 0:
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
            result['name'] = as_name + " (" + as_code + ")" + ' - ' + type_code 
        return {'value': result}

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
                return last_move_line, True
            else:
                return False, False
        return False, True

    def _compute_period(self, cr, uid, method, period, context={}):
        if (period.date_start < method.period_id.date_start) \
                or ((mx.DateTime.strptime(period.date_stop, '%Y-%m-%d').month % (12 / method.method_period)) != 0):
            return False
        return True

    def _compute_move(self, cr, uid, method, period, date, usage_id, last_move_line, context={}):
        result = []
        gross = method.value_total - method.value_salvage
        to_writeoff = method.value_residual - method.value_salvage 
        if usage_id:                # Units of Production method
            amount = gross * self.pool.get('account.asset.method.usage').browse(cr, uid, usage_id, context).usage / method.life
            if amount > to_writeoff:
                amount = to_writeoff
        else:
#            total = 0.0
            depr_entries_made = 0
            for move in method.entry_ids:
#            if move.account_id == method.account_asset_id:
#                total += move.debit - move.credit
                if move.account_id == method.account_actif_id:
#                    to_writeoff -= move.debit
                    depr_entries_made += 1 
#            total -= method.value_salvage
    
#        for move in method.entry_asset_ids:
#            if move.account_id == method.account_expense_id:
#                total += move.debit-move.credit
#        entries_made = (len(method.entry_asset_ids)/2)   # GG fix needed for declining-balance
            intervals = method.method_delay - depr_entries_made     # GG fix
            if intervals == 1:
                amount = to_writeoff
            else:
                if method.method == 'linear':
                    amount = to_writeoff / intervals
                elif method.method == 'progressive':                          # GG fix begin 
                    amount = to_writeoff * method.method_progress_factor
                elif method.method == 'decbalance':
#                    period_begin = mx.DateTime.strptime(period.date_start, '%Y-%m-%d')
                    period_end = mx.DateTime.strptime(period.date_stop, '%Y-%m-%d')
#                    period_duration = period_end.month - period_begin.month + 1 
#                    intervals_per_year = 12 / period_duration / method.method_period
                    if depr_entries_made == 0:                              # First year
#                        remaining_intervals = abs((12 - period_end.month) / 12 / method.method_period)
                        amount = to_writeoff * method.method_progress_factor / method.method_period 
#* remaining_intervals / method.method_period) / remaining_intervals
                    elif (12 / period_end.month) == method.method_period:                      # Beginning of the year
                        amount = to_writeoff * method.method_progress_factor / method.method_period
                        if amount < (gross / method.method_delay):   # In declining-balance when amount less than amount for linear it switches to linear
                            amount = gross / method.method_delay
                    else:                                              # In other cases repeat last entry
#                        cr.execute("SELECT m.id, m.debit \
#                                    FROM account_move_line AS m \
#                                        LEFT JOIN account_move_asset_entry_rel AS r \
#                                        ON m.id = r.move_id \
#                                            LEFT JOIN account_asset_method AS p \
#                                            ON p.asset_id = r.asset_method_id \
#                                        WHERE p.asset_id = %s \
#                                        ORDER BY m.id DESC", (method.asset_id.id,))
#                        amount = cr.fetchone()[1]
#                        raise osv.except_osv('Error !', 'last %s'%last_move_line.debit) 
                        amount = last_move_line.debit
                    if to_writeoff < amount:
                        amount = to_writeoff
                elif method.method == 'syd':
                    pass

                                                                             # GG fix end
        move_id = self.pool.get('account.move').create(cr, uid, {
            'journal_id': method.journal_id.id,
            'period_id': period.id,
            'date': date,
            'name': '/',                         # GG fix, was 'name': method.name or method.asset_id.name,
            'ref': method.asset_id.code
        })
        result = [move_id]
        id = self.pool.get('account.move.line').create(cr, uid, {
            'name': method.name or method.asset_id.name,
            'move_id': move_id,
            'account_id': method.account_expense_id.id,
            'credit': amount,      #   >0 and amount or 0.0,       # GG fix
#            'debit': amount<0 and -amount or 0.0,       # GG fix
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
            'debit': amount,            #      >0 and amount or 0.0,            # GG fix
#            'credit': amount<0 and -amount or 0.0,          # GG fix
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
        if (to_writeoff == amount): 
            self.pool.get('account.asset.method')._close(cr, uid, method, context)
            return result
        return result

    def _compute_entries(self, cr, uid, method, period_id, date, context={}):
        if method.state=='open':
            period = self.pool.get('account.period').browse(cr, uid, period_id, context)
            result = []
            usage_id = False
            period_ok = False
            last_move_line, compute_period = self._compute_last_calculated(cr, uid, method, period, context)
            if method.method == 'uop':
                usage_ids = self.pool.get('account.asset.method.usage').search(cr, uid, [('period_id','=',period_id),('asset_method_id','=',method.id)])
                usage_id = usage_ids and usage_ids[0] or False
            else:
                period_ok = self._compute_period(cr, uid, method, period, context)
            if (period_ok or usage_id) and compute_period:
                result += self._compute_move(cr, uid, method, period, date, usage_id, last_move_line, context)
        return result

    '''
    def _compute_entries(self, cr, uid, method, period_id, date, context={}):
        result = []
        date_start = self.pool.get('account.period').browse(cr, uid, period_id, context).date_start
        if method.state=='open':
            period = self._compute_period(cr, uid, method, context)
            if period and (period.date_start<=date_start):
                result += self._compute_move(cr, uid, method, period, date, context)
        return result
    '''

account_asset_method()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Asset Depr. Method'),
    }
account_move_line()

class account_asset_history(osv.osv):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _columns = {
        'name': fields.char('History name', size=64, select=1),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'date': fields.date('Date', required=True),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True),
        'asset_method_id': fields.many2one('account.asset.method', 'Method', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'method_delay': fields.integer('Number of Interval'),
        'method_period': fields.integer('Period per Interval'),
        'method_end': fields.date('Ending Date'),
        'note': fields.text('Note'),
    }
    _defaults = {
        'date': lambda *args: time.strftime('%Y-%m-%d'),
        'user_id': lambda self,cr, uid,ctx: uid
    }
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


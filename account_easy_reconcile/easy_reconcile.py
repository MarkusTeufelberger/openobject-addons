# -*- coding: utf-8 -*-
##############################################################################
#
#    Account easy reconcile module for OpenERP
#    Copyright (C) 2010 -2011 Akretion Sébastien BEAU 
#                                   <sebastien.beau@akretion.com>
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

from osv import fields,osv
from tools.translate import _
import time
import string

class account_easy_reconcile_method(osv.osv):
    _name = 'account.easy.reconcile.method'
    _description = 'reconcile method for account_easy_reconcile'

    def onchange_name(self, cr, uid, id, name, write_off, context=None):
        if name in ['action_rec_auto_name', 'action_rec_auto_partner']:
            if write_off>0:
                return {'value' : {'require_write_off' : True, 'require_account_id' : True, 'require_journal_id' : True}}
            return {'value' : {'require_write_off' : True}}
        return {}

    def onchange_write_off(self, cr, uid, id, name, write_off, context=None):
        if name in ['action_rec_auto_name', 'action_rec_auto_partner']:
            if write_off>0:
                return {'value' : {'require_account_id' : True, 'require_journal_id' : True}}
            else:
                return {'value' : {'require_account_id' : False, 'require_journal_id' : False}}
        return {}  
    
    def _get_rec_method(self, cr, uid, context=None):
        return [
            ('action_rec_auto_name', 'Simple method based on amount and name'),
            ('action_rec_auto_partner', 'Simple method based on amount and partner'),
            ]

    _columns = {
            'name': fields.selection(_get_rec_method, 'Type', size=128, required=True),
            'sequence': fields.integer('Sequence', required=True, help="The sequence field is used to order the reconcile method"),
            'write_off': fields.float('Write off Value'),
            'account_lost_id': fields.many2one('account.account', 'Account Lost'),
            'account_profit_id': fields.many2one('account.account', 'Account Profit'),
            'journal_id': fields.many2one('account.journal', 'Journal'),
            'require_write_off' : fields.boolean('Require Write-off'),
            'require_account_id' : fields.boolean('Require Account'),
            'require_journal_id' : fields.boolean('Require Journal'),
            'date_base_on': fields.selection([('newest', 'the most recent'), ('actual', 'today'), ('credit_line', 'credit line date'), ('debit_line', 'debit line date')], 'Date Base On'),
            'filter' : fields.char('Filter', size=128),
            }
        

    _defaults = {
        'write_off': lambda *a: 0,
                }

    _order = 'sequence'


account_easy_reconcile_method()

class account_easy_reconcile(osv.osv):
    _name = 'account.easy.reconcile'
    _description = 'account easy reconcile'
    
    def _get_unrec_number(self, cr, uid, ids, name, arg, context=None):
        obj_move_line = self.pool.get('account.move.line')
        res={}
        for task in self.read(cr, uid, ids, ['account'], context=context):
            res[task['id']] = len(obj_move_line.search(cr, uid, [('account_id', '=', task['account'][0]), ('reconcile_id', '=', False)], context=context))
        return res
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'account': fields.many2one('account.account', 'Account', required=True),
        'reconcile_method': fields.one2many('account.easy.reconcile.method', 'task_id', 'Method'),
        'scheduler': fields.many2one('ir.cron', 'scheduler', readonly=True),
        'rec_log': fields.text('log', readonly=True),
        'unreconcile_entry_number': fields.function(_get_unrec_number, method=True, type='integer', string='Unreconcile Entries'),
    }
    
    def rec_auto_lines_simple(self, cr, uid, lines, context=None):
        if not context:
            context={}
        count=0
        res=0
        max = context.get('write_off', 0) + 0.001
        while (count<len(lines)):
            for i in range(count+1, len(lines)):
                if lines[count][0] != lines[i][0]:
                    break

                check = False
                if lines[count][1] > 0 and lines[i][2] > 0:
                    credit_line = lines[count]
                    debit_line = lines[i]
                    check =True
                elif lines[i][1] > 0  and lines[count][2] > 0:
                    credit_line = lines[i]
                    debit_line = lines[count]
                    check=True

                if check and abs(credit_line[1] - debit_line[2]) <= max:
                    if context.get('write_off', 0) > 0 and abs(credit_line[1] - debit_line[2]) > 0.001:
                        if credit_line[1] < debit_line[2]:
                            writeoff_account_id = context.get('account_profit_id',False)
                        else:
                            writeoff_account_id = context.get('account_lost_id',False)

                    #context['date_base_on'] = 'credit_line'
                    context['comment'] = _('Write-Off') + ' ' + credit_line[0]

                    if context.get('date_base_on', False) == 'credit_line':
                        print 'credit'
                        date = credit_line[4]
                    elif context.get('date_base_on', False) == 'debit_line':
                        print 'debit'
                        date = debit_line[4]
                    elif context.get('date_base_on', False) == 'newest':
                        print 'newest', (credit_line[4] > debit_line[4]) and credit_line[4] or debit_line[4]
                        print credit_line[4], debit_line[4]
                        date = (credit_line[4] > debit_line[4]) and credit_line[4] or debit_line[4]
                    else:
                        print 'none'
                        date = None

                    context['date_p'] = date
                    period_id = self.pool.get('account.period').find(cr, uid, dt=date, context=context)[0]

                    self.pool.get('account.move.line').reconcile(cr, uid, [lines[count][3], lines[i][3]], writeoff_acc_id=writeoff_account_id, writeoff_period_id=period_id, writeoff_journal_id=context.get('journal_id'), context=context)
                    del lines[i]
                    res+=2
                    break
            count+=1
        return res
     

    def get_params(self, cr, uid, account_id, context):
        print 'filter', context['filter'], type(context['filter'])
        (qu1, qu2, tables) = self.pool.get('account.move.line')._where_calc(cr, uid, context['filter'], context=context)
        print qu1, qu2
        if len(qu1):
            qu1 = ' and ' + string.join(qu1, ' and ')
            qu2 = (account_id,) + tuple(qu2)
        else:
            qu1 = ''
            qu2 = (account_id,)
        return qu1, qu2


    def action_rec_auto_name(self, cr, uid, account_id, context):
        (qu1, qu2) = self.get_params(cr, uid, account_id, context)
        cr.execute("""
            SELECT name, credit, debit, id, date
            FROM account_move_line
            WHERE account_id=%s
            AND reconcile_id IS NULL
            AND name IS NOT NULL""" + qu1 + " ORDER BY name",
            qu2)
        lines = cr.fetchall()
        return self.rec_auto_lines_simple(cr, uid, lines, context)
  

    def action_rec_auto_partner(self, cr, uid, account_id, context):
        (qu1, qu2) = self.get_params(cr, uid, account_id, context)
        cr.execute("""
            SELECT partner_id, credit, debit, id, date
            FROM account_move_line
            WHERE account_id=%s
            AND reconcile_id IS NULL
            AND partner_id IS NOT NULL""" + qu1 + " ORDER BY partner_id",
            qu2)
        lines = cr.fetchall()
        return self.rec_auto_lines_simple(cr, uid, lines, context)
    
    def action_rec_auto(self, cr, uid, ids, context=None):
        if not context:
            context={}
        for id in ids:
            easy_rec = self.browse(cr, uid, id, context)
            total_rec=0
            details = ''
            count = 0
            for method in easy_rec.reconcile_method:
                count += 1
                context.update({'date_base_on' : method.date_base_on, 'filter' : eval(method.filter or '[]'), 'write_off': (method.write_off>0 and method.write_off) or 0, 'account_lost_id':method.account_lost_id.id, 'account_profit_id':method.account_profit_id.id, 'journal_id':method.journal_id.id})
                res = eval('self.'+ str(method.name) +'(cr, uid, ' + str(easy_rec.account.id) +', context)')
                details += _(' method ') + str(count) + ' : ' + str(res) + _(' lines') +' |'
            log = self.read(cr, uid, id, ['rec_log'], context=context)['rec_log']
            log_line = log and log.split("\n") or []
            log_line[0:0] = [time.strftime('%Y-%m-%d %H:%M:%S') + ' : ' + str(total_rec) + _(' lines have been reconciled ('+ details[0:-2] + ')')]
            log = "\n".join(log_line)
            self.write(cr, uid, id, {'rec_log' : log}, context=context)
        return True
    
account_easy_reconcile()


class account_easy_reconcile_method(osv.osv):
    _inherit = 'account.easy.reconcile.method'

    _columns = {
            'task_id' : fields.many2one('account.easy.reconcile', 'Task', required=True, ondelete='cascade'),
        }
account_easy_reconcile_method()

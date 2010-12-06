# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Created by Luc De Meyer
#    Copyright (c) 2010 Noviat nv/sa (www.noviat.be). All rights reserved.
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

import time
from osv import osv, fields
import netsvc
from tools.translate import _
logger=netsvc.Logger()

class account_coda(osv.osv):
    _name = 'account.coda'
    _description = 'Object to store CODA Data Files'
    _order = 'coda_creation_date desc'
    _columns = {
        'name': fields.char('CODA Filename',size=128, readonly=True),
        'coda_data': fields.binary('CODA File', readonly=True),
        'statement_ids': fields.one2many('coda.bank.statement','coda_id','Generated CODA Bank Statements', readonly=True),
        'note': fields.text('Import Log', readonly=True),
        'coda_creation_date': fields.date('CODA Creation Date', readonly=True, select=True),
        'date': fields.date('Import Date', readonly=True, select=True),
        'user_id': fields.many2one('res.users','User', readonly=True, select=True),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'user_id': lambda self,cr,uid,context: uid,
    }        
    _sql_constraints = [
        ('coda_uniq', 'unique (name, coda_creation_date)', 'This CODA has already been imported !')
    ]  
account_coda()

class account_coda_trans_type(osv.osv):  
    _name = 'account.coda.trans.type'
    _description = 'CODA transaction type'
    _rec_name = 'type' 
    _columns = {
        'type': fields.char('Transaction Type', size=1, required=True),
        'parent_id': fields.many2one('account.coda.trans.type', 'Parent'),
        'description': fields.text('Description', translate=True),
    }
account_coda_trans_type()

class account_coda_trans_code(osv.osv):  
    _name = 'account.coda.trans.code'
    _description = 'CODA transaction code'
    _rec_name = 'code' 
    _columns = {
        'code': fields.char('Code', size=2, required=True, select=1),
        'type': fields.selection([
                ('code', 'Transaction Code'),
                ('family', 'Transaction Family')], 
                'Type', required=True, select=1), 
        'parent_id': fields.many2one('account.coda.trans.code', 'Family', select=1),
        'description': fields.char('Description', size=128, translate=True, select=2),
        'comment': fields.text('Comment', translate=True),
    }
account_coda_trans_code()

class account_coda_trans_category(osv.osv):  
    _name = 'account.coda.trans.category'
    _description = 'CODA transaction category'
    _rec_name = 'category' 
    _columns = {
        'category': fields.char('Transaction Category', size=3, required=True),
        'description': fields.char('Description', size=256, translate=True),
    }
account_coda_trans_category()

class account_coda_comm_type(osv.osv):  
    _name = 'account.coda.comm.type'
    _description = 'CODA structured communication type'
    _rec_name = 'code' 
    _columns = {
        'code': fields.char('Structured Communication Type', size=3, required=True, select=1),
        'description': fields.char('Description', size=128, translate=True),
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)','The Structured Communication Code must be unique !')
        ]
account_coda_comm_type()

class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
        'iban': fields.char('IBAN', size=34, 
                help="International Bank Account Number, used for bank journals."
                     "\nThe CODA import function will select the bank journal based on this number."
                     "\nEnter the IBAN number in uppercase and without spaces."),
    }
account_journal()

class coda_bank_statement(osv.osv):
    _name = 'coda.bank.statement' 
    _description = 'CODA Bank Statement'    
    
    def _default_journal_id(self, cr, uid, context={}):
        if context.get('journal_id', False):
            return context['journal_id']
        return False

    def _end_balance(self, cursor, user, ids, name, attr, context=None):
        res = {}
        statements = self.browse(cursor, user, ids, context=context)
        for statement in statements:
            res[statement.id] = statement.balance_start
            for line in statement.line_ids:
                    res[statement.id] += line.amount
        for r in res:
            res[r] = round(res[r], 2)
        return res

    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False

    def _currency(self, cursor, user, ids, name, args, context=None):
        res = {}
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        default_currency = res_users_obj.browse(cursor, user,
                user, context=context).company_id.currency_id
        for statement in self.browse(cursor, user, ids, context=context):
            currency = statement.journal_id.currency
            if not currency:
                currency = default_currency
            res[statement.id] = currency.id
        currency_names = {}
        for currency_id, currency_name in res_currency_obj.name_get(cursor,
                user, [x for x in res.values()], context=context):
            currency_names[currency_id] = currency_name
        for statement_id in res.keys():
            currency_id = res[statement_id]
            res[statement_id] = (currency_id, currency_names[currency_id])
        return res

    _order = 'date desc'
    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True),
        'date': fields.date('Date', required=True, readonly=True),
        'coda_id': fields.many2one('account.coda', 'CODA Data File'),        
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True,
            domain=[('type', '=', 'cash')]),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True),
        'balance_start': fields.float('Starting Balance', digits=(16,2), readonly=True),
        'balance_end_real': fields.float('Ending Balance', digits=(16,2), readonly=True),
        'balance_end': fields.function(_end_balance, method=True, string='Balance'),        
        'line_ids': fields.one2many('coda.bank.statement.line',
            'statement_id', 'CODA Bank Statement lines', readonly=True),
        'state': fields.selection([('draft', 'Draft'),('done', 'Done')],
            'State', required=True, readonly=True),
        'currency': fields.function(_currency, method=True, string='Currency',
            type='many2one', relation='res.currency'),
    }
    _defaults = {
        'state': lambda *a: 'draft',
        'journal_id': _default_journal_id,
        'period_id': _get_period,
    }

    def button_generate(self, cr, uid, ids, context={}):       
        for statement in self.browse(cr, uid, ids, context):
            try:
                
                bk_st_id = self.pool.get('account.bank.statement').create(cr, uid, {
                    'journal_id': statement.journal_id.id,
                    'coda_statement_id': ids[0],
                    'date': statement.date,
                    'period_id': statement.period_id.id,
                    'balance_start': statement.balance_start,
                    'balance_end_real': statement.balance_end_real,
                    'state': 'draft',
                })
                line_ids = statement.line_ids
                for rec in line_ids:
                    line = self.pool.get('coda.bank.statement.line').browse(cr, uid, rec.id, context=context)                  
                    if line.type in ['information', 'communication', 'globalisation']:
                        pass
                    else:
                        st_line_id = self.pool.get('account.bank.statement.line').create(cr, uid, {
                                   'name': line.name,
                                   'type' : line.type,
                                   'date': line.date,
                                   'amount': line.amount,
                                   'partner_id': line.partner_id and line.partner_id.id,
                                   'account_id': line.account_id and line.account_id.id,
                                   'statement_id': bk_st_id,
                                   'note': line.note,
                                   'ref': line.ref,
                                   })
    
                cr.commit()
    
            except osv.except_osv, e:
                cr.rollback()
                err_log = '\n\nApplication Error : ' + str(e)
                raise osv.except_osv(_('Error !'),err_log)
    
            except Exception, e:
                cr.rollback()
                err_log = '\n\nSystem Error : ' +str(e)
                raise osv.except_osv(_('Error !'),err_log)

            except :
                cr.rollback()
                err_log = '\n\nUnknown Error'
                raise osv.except_osv(_('Error !'),err_log)

        self.write(cr, uid, ids, {'state':'done'}, context=context)
        return True

    def button_cancel(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'draft'}, context=context)
        return True

 
coda_bank_statement()

class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'
    _columns = {
        'coda_statement_id': fields.many2one('coda.bank.statement', 'associated CODA bank statement'),
    }        
account_bank_statement()

class coda_bank_statement_line(osv.osv):
    _name = 'coda.bank.statement.line'     
    _order = 'sequence'   
    _description = "CODA Bank Statement Line"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'sequence': fields.integer('Sequence'),
        'date': fields.date('Date', required=True),
        'account_id': fields.many2one('account.account','Account'),     # remove required=True
        'type': fields.selection([
            ('supplier','Supplier'),
            ('customer','Customer'),
            ('general','General'),
            ('globalisation','Globalisation'),            
            ('information','Information'),    
            ('communication','Free Communication'),          
            ], 'Type', required=True),
        'globalisation_level': fields.integer('Globalisation Level', 
                help="The value which is mentioned (1 to 9), specifies the hierarchy level"
                     " of the globalisation of which this record is the first."
                     "\nThe same code will be repeated at the end of the globalisation."),
        'globalisation_amount': fields.float('Globalisation Amount'),                                                           
        'amount': fields.float('Amount'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'statement_id': fields.many2one('coda.bank.statement', 'CODA Bank Statement',
            select=True, required=True, ondelete='cascade'),
        'ref': fields.char('Ref.', size=32),
        'note': fields.text('Notes'),
    }
coda_bank_statement_line()       

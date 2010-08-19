# -*- coding: utf-8 -*-
##############################################
# ChriCar Beteiligungs- und Beratungs- GmbH
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#
###############################################
import time
import netsvc
from osv import fields, osv

from tools.misc import currency
from tools.translate import _


# name should hold the period name + special names

class account_period_sum(osv.osv):
    _name = "account.account_period_sum"
    _description = "Account Period Sum"
    _columns = {
      'name'               : fields.char    ('Period', size=16,reaodonly=True),
      'account_id'         : fields.many2one('account.account', 'Account', required=True,ondelete="cascade",readonly=True),
      'period_id'          : fields.many2one('account.period' , 'Period' , required=True,ondelete="cascade",readonly=True),
      'sum_fy_period_id'   : fields.integer ('Account FY id'             , required=True,                   readonly=True),
      'debit'              : fields.float   ('Debit', digits=(16,2), required=True,readonly=True),
      'credit'             : fields.float   ('Credit', digits=(16,2), required=True,readonly=True),
    }
    _order = 'name asc'

account_period_sum()


class account_fy_period_sum(osv.osv):
    _name = "account.account_fy_period_sum"
    _description = "Account Fiscalyear Period Sum"
    _auto = False
    _columns = {
      'name'               : fields.char    ('Period', size=16       ,readonly=True),
      'account_id'         : fields.many2one('account.account', 'Account',readonly=True),
      'period_id'          : fields.many2one('account.period' , 'Period' ,readonly=True),
      'debit'              : fields.float   ('Debit', digits=(16,2) ,readonly=True),
      'credit'             : fields.float   ('Credit', digits=(16,2),readonly=True),
      'balance'            : fields.float   ('Balance', digits=(16,2)    ,readonly=True),
      'sum_fy_period_id'   : fields.integer ('Account FY id'             ,readonly=True),
      'date_start'	   : fields.date    ('Date Start',readonly=True),
      'date_stop'	   : fields.date    ('Date Stop' ,readonly=True),
      'move_line_ids'      : fields.one2many('account.move.line','account_period_sum_id','Account_moves'),
    }
    _order = 'date_start asc,name'
    def init(self, cr):    
      cr.execute("""
      create or replace view account_account_fy_period_sum
      as
      select s.id  as id,
             s.name,
             account_id,period_id,
             debit as debit ,credit as credit,
             debit-credit as balance,
             sum_fy_period_id as sum_fy_period_id,
	         p.date_start,p.date_stop
        from account_account_period_sum s,
	     account_period p,
	     account_fiscalyear y
       where p.id = s.period_id
         and y.id = p.fiscalyear_id""")
       
account_fy_period_sum()




class account_fiscalyear_sum(osv.osv):
    _name = "account.account_fiscalyear_sum"
    _description = "Account Fiscalyear Sum"
    _auto = False
    _columns = {
      'account_id'         : fields.many2one('account.account', 'Account'       ,readonly=True),
      'fiscalyear_id'      : fields.many2one('account.fiscalyear' , 'Fiscal Year',readonly=True),
      'name'               : fields.char    ('Fiscal Year', size =16,           readonly=True),
      'debit'              : fields.float   ('Debit', digits=(16,2),            readonly=True ),
      'credit'             : fields.float   ('Credit', digits=(16,2),           readonly=True),
      'balance'            : fields.float   ('Balance', digits=(16,2),          readonly=True),
      'sum_fy_period_ids'  : fields.one2many('account.account_fy_period_sum','sum_fy_period_id','Fiscal Year Period Sum'),
      'date_start'	       : fields.date    ('Date Start',readonly=True),
      'date_stop'	       : fields.date    ('Date Stop' ,readonly=True),

    }
    _order = 'name desc'


    def init(self, cr):    
            cr.execute("""create or replace view account_account_fiscalyear_sum
            as select 
            sum_fy_period_id as id,
            account_id,
            to_char(y.date_stop,'YYYY') || case when to_char(y.date_stop,'MM')  != '12'
                                            then  '-'||to_char(y.date_stop,'MM')
                                            else '' end as name,
            y.id as fiscalyear_id,
            sum(debit) as debit,
            sum(credit) as credit,
            sum(debit) - sum(credit) as balance,
            y.date_start,y.date_stop
            from account_account_period_sum s,
                account_period p,
                account_fiscalyear y
            where p.id = s.period_id
            and y.id = p.fiscalyear_id
            group by sum_fy_period_id,s.account_id,y.id,
	        to_char(y.date_stop,'YYYY') || case when to_char(y.date_stop,'MM')  != '12'
                                            then  '-'||to_char(y.date_stop,'MM')
                                            else '' end	    ,
	        y.date_start,y.date_stop""")
  
account_fiscalyear_sum()


def _code_get(self, cr, uid, context={}):
        acc_type_obj = self.pool.get('account.account.type')
        ids = acc_type_obj.search(cr, uid, [])
        res = acc_type_obj.read(cr, uid, ids, ['code', 'name'], context)
        return [(r['code'], r['name']) for r in res]

class account_account_with_postings(osv.osv):
    _name = "account.account_with_postings"
    _description = "Accounts with Postings"
    _auto = False
    _columns = {
      'code'              : fields.char     ('Code', size=64, readonly=True),
      'name'              : fields.char     ('Name', size=128, readonly=True),
      'type'              : fields.selection(_code_get, 'Account Type', readonly=True),
      'shortcut'          : fields.char     ('Shortcut', size=12,readonly=True),
      'sum_period_ids'    : fields.one2many ('account.account_period_sum','account_id','Sum Periods'),
      'sum_fy_period_ids' : fields.one2many ('account.account_fy_period_sum','account_id','Sum Fiscal Year Periods'),
      'sum_fiscalyear_ids': fields.one2many ('account.account_fiscalyear_sum','account_id','Sum Fiscal Years'),
    }
    _order = 'code,name'
    
    def init(self, cr):
            cr.execute("""create or replace view account_account_with_postings
            as select 
            a.id,a.code,a.name,a.company_id,a.shortcut,t.sign,a.currency_id,a.note,t.close_method,a.active,a.type,a.reconcile
            from account_account a,
                 account_account_type t  
            where user_type = t.id
              and exists ( select 'x' from account_account_period_sum where account_id = a.id);
            """)
account_account_with_postings()


#
# sum_period_id must be a get_id (account, period) to link move_lines to periods
#
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _columns = {
        'account_period_sum_id': fields.many2one('account.account_period_sum', 'Period Sum', select=1),
    }
account_move_line()

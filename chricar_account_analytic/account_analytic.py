# -*- coding: utf-8 -*-

#!/usr/bin/python
# -*- encoding: utf-8 -*-
##############################################
#
# ChriCar Beteiligungs- und Beratungs- GmbH
# Copyright (C) ChriCar Beteiligungs- und Beratungs- GmbH
# all rights reserved
# created 2009-08-18 23:44:30+02
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/> or
# write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################
import time
from osv import fields,osv
import pooler



class account_account(osv.osv):
    _inherit = "account.account"



    _columns = {
     'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account', select=True,
          help="provide Analytic Account only for default and fixed"),
     'account_analytic_usage': fields.selection([
            ('fixed','Fixed'),
            ('default','Default'),
            ('mandatory','Mandatory'),
            ('optional','Optional'),
            ('none','Not allowed'),
            ], 'Analytic Account Usage', help="""This type is used to differenciate types with
special effects in Open ERP:
for P&L accounts
* fixed: will be used and user can not change it
* default: will be proposed and user can change it
* mandatory: user must supply analytic account
for balance accounts
* mandatory: user must supply analytic account
* optional: user may supply analytic account
* none: no analytic account allowed""",
            ) ,

    }

    def _analytic_account_type(self, cr, uid, context={}):
        account = self.pool.get('account.account').browse(cr, uid, uid, context=context)
        if account.account_analytic_usage:
            return
        if account.user_type.close_method == 'none':
            # P&L
            return 'mandatory'
        else:
            return 'none'
            
    _defaults = {
      'account_analytic_usage' : _analytic_account_type,
    }


    def _check_analytic_account_usage(self, cr, uid, ids):
         account = self.browse(cr, uid, ids[0])
         if account.user_type.close_method == 'none' and account.account_analytic_usage not in ('mandatory','default','fixed'):
                return False
         # FIXME - do we need the following check? -
         #if account.user_type.close_method != 'none' and account.account_analytic_usage not in ('mandatory','optional','none'):
         #       return False
         return True

    def _check_analytic_account_id(self, cr, uid, ids):
         account = self.browse(cr, uid, ids[0])
         if not account.account_analytic_id and account.account_analytic_usage in ('default','fixed'):
                return False
         # FIXME - do we need the following check? -
         if account.account_analytic_id and account.account_analytic_usage not in ('default','fixed'):
                return False
         return True


    _constraints = [
        (_check_analytic_account_usage,
            'You must assign a correct analytic account usage', ['account_analytic_usage']),
        (_check_analytic_account_id,
            'You must define an analytic account for fixed and default, else nothing', ['account_analytic_id']),

        ]



    def init(self, cr):
      # We set some resonable values
      # P & L accounts - mandatory
      # other no analytic account
      cr.execute("""
         update account_account
           set account_analytic_usage = (
                select distinct
                   case when close_method = 'none' and code != 'view' then 'mandatory' when code = 'view'  then null else 'none' end
                  from account_account_type aat
                 where aat.id = user_type)
          where account_analytic_usage is null;
      """)


account_account()


class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def _check_analytic_account(self, cr, uid, ids):
        for move in self.browse(cr, uid, ids):
            # FIXME - does not write the found value
            #if not move.analytic_account_id and move.account_id.account_analytic_usage in ['default','fixed']:
            #    move.account_id.analytic_account_id = move.account_id.account_analytic_id
            #    return True
            if not move.analytic_account_id and move.account_id.account_analytic_usage in ['mandatory','default','fixed']:
                return False
            if move.analytic_account_id and move.account_id.account_analytic_usage in ['none']:
                return False
        return True

    _constraints = [
        (_check_analytic_account,
            'You must assign an analytic account using this account', ['analytic_account_id'] ),
        ]

account_move_line()


class account_bank_statement_line(osv.osv):
    _inherit = "account.bank.statement.line"

    def _check_analytic_account(self, cr, uid, ids):
        for move in self.browse(cr, uid, ids):
            if not move.account_analytic_id and move.account_id.account_analytic_usage in ['default','fixed']:
                move.account_analytic_id = move.account_id.account_analytic_id
                return True
            if not move.account_analytic_id and move.account_id.account_analytic_usage in ['mandatory','default','fixed']:
                return False
            if move.account_analytic_id and move.account_id.account_analytic_usage in ['none']:
                return False
        return True

    _constraints = [
        (_check_analytic_account,
            'You must assign an analytic account using this account', ['account_analytic_id'] ),
        ]

account_bank_statement_line()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"


    def _check_analytic_account(self, cr, uid, ids):
        for move in self.browse(cr, uid, ids):
            # FIXME - does not write the found value
            #if not move.account_analytic_id and move.account_id.account_analytic_usage in ['default','fixed']:
            #    move.account_analytic_id = move.account_id.account_analytic_id
            #    res = {'value': {'account_analytic_id' : move.account_id.account_analytic_id.id }}
            #    return res
            if not move.account_analytic_id and move.account_id.account_analytic_usage in ['mandatory','default','fixed']:
                return False
            if move.account_analytic_id and move.account_id.account_analytic_usage in ['none']:
                return False
        return True

    _constraints = [
        (_check_analytic_account,
            'You must assign an analytic account using this account', ['account_analytic_id'] ),
        ]

account_invoice_line()

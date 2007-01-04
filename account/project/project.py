##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id$
#
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
##############################################################################

import time
import operator

from osv import fields
from osv import osv

#
# Model definition
#

class account_analytic_account(osv.osv):
	_name = 'account.analytic.account'

	def _credit_calc(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for account in self.browse(cr, uid, ids):
			node_balance = reduce(operator.add, [-line.amount for line in account.line_ids if line.amount<0], 0)
			child_balance = reduce(operator.add, [child.credit for child in account.child_ids], 0)
			res[account.id] = node_balance + child_balance
		for id in ids:
			res[id] = round(res.get(id, 0.0),2)
		return res

	def _debit_calc(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for account in self.browse(cr, uid, ids):
			node_balance = reduce(operator.add, [line.amount for line in account.line_ids if line.amount>0], 0)
			child_balance = reduce(operator.add, [child.debit for child in account.child_ids], 0)
			res[account.id] = node_balance + child_balance
		for id in ids:
			res[id] = round(res.get(id, 0.0),2)
		return res

	def _balance_calc(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for account in self.browse(cr, uid, ids):
			node_balance = reduce(operator.add, [line.amount for line in account.line_ids], 0)
			child_balance = reduce(operator.add, [child.balance for child in account.child_ids], 0)
			res[account.id] = node_balance + child_balance
		for id in ids:
			res[id] = round(res.get(id, 0.0),2)
		return res

	def _quantity_calc(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for account in self.browse(cr, uid, ids):
			node_balance = reduce(operator.add, [line.unit_amount for line in account.line_ids], 0)
			child_balance = reduce(operator.add, [child.quantity for child in account.child_ids], 0)
			res[account.id] = node_balance + child_balance
		for id in ids:
			res[id] = round(res.get(id, 0.0),2)
		return res

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['name','parent_id'], context)
		res = []
		for record in reads:
			name = record['name']
			if record['parent_id']:
				name = record['parent_id'][1]+' / '+name
			res.append((record['id'], name))
		return res

	def _complete_name_calc(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = self.name_get(cr, uid, ids)
		return dict(res)


	_columns = {
		'name' : fields.char('Account name', size=64, required=True),
		'complete_name': fields.function(_complete_name_calc, method=True, type='char', string='Account Name'),
		'code' : fields.char('Account code', size=24),
		'active' : fields.boolean('Active'),
		'type': fields.selection([('view','View'), ('normal','Normal')], 'type'),
		'description' : fields.text('Description'),
		'parent_id': fields.many2one('account.analytic.account', 'Parent Cost account', select=True),
		'child_ids': fields.one2many('account.analytic.account', 'parent_id', 'Childs Accounts'),
		'line_ids': fields.one2many('account.analytic.line', 'account_id', 'Analytic entries'),
		'balance' : fields.function(_balance_calc, method=True, type='float', string='Balance'),
		'debit' : fields.function(_debit_calc, method=True, type='float', string='Balance'),
		'credit' : fields.function(_credit_calc, method=True, type='float', string='Balance'),
		'quantity': fields.function(_quantity_calc, method=True, type='float', string='Quantity'),
		'quantity_max': fields.float('Maximal quantity'),
		'partner_id' : fields.many2one('res.partner', 'Associated partner'),
		'contact_id' : fields.many2one('res.partner.address', 'Contact'),
		'user_id' : fields.many2one('res.users', 'Account Manager'),
		'date_start': fields.date('Date Start'),
		'date': fields.date('Date End'),
		'stats_ids': fields.one2many('report.hr.timesheet.invoice.journal', 'account_id', string='Statistics', readonly=True),
	}

	_defaults = {
		'active' : lambda *a : True,
		'type' : lambda *a : 'normal',
	}

	_order = 'parent_id desc,code'

	def create(self, cr, uid, vals, ctx={}):
		parent_id = vals.get('parent_id', 0)
		if ('code' not in vals or not vals['code']) and not parent_id:
			vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'account.analytic.account')
		return super(account_analytic_account, self).create(cr, uid, vals, ctx)


	def on_change_parent(self, cr, uid, id, parent_id):
		if not parent_id:
			return {'value': {'code': False, 'partner_id': ''}}
		parent = self.read(cr, uid, [parent_id], ['partner_id','code'])[0]
		childs = self.search(cr, uid, [('parent_id', '=', parent_id), ('active', '=', 1)]) + self.search(cr, uid, [('parent_id', '=', parent_id), ('active', '=', 0)])
		numchild = len(childs)
		if parent['partner_id']:
			partner = parent['partner_id'][0]
		else:
			partner = False
		res = {'value' : {'code' : '%s - %03d' % (parent['code'] or '', numchild + 1), 'partner_id' : partner}}
		return res

	def name_search(self, cr, uid, name, args=[], operator='ilike', context={}):
		account = self.search(cr, uid, [('code', '=', name)]+args)
		if not account:
			account = self.search(cr, uid, [('name', 'ilike', '%%%s%%' % name)]+args)
			newacc = account
			while newacc:
				newacc = self.search(cr, uid, [('parent_id', 'in', newacc)]+args)
				account+=newacc
		return self.name_get(cr, uid, account, context=context)

account_analytic_account()


class account_analytic_journal(osv.osv):
	_name = 'account.analytic.journal'
	_columns = {
		'name' : fields.char('Journal name', size=64, required=True),
		'code' : fields.char('Journal code', size=8),
		'active' : fields.boolean('Active'),
		'type': fields.selection([('sale','Sale'), ('purchase','Purchase'), ('cash','Cash'), ('general','General'), ('situation','Situation')], 'Type', size=32, required=True, help="Gives the type of the analytic journal. When a document (eg: an invoice) needs to create analytic entries, Tiny ERP will look for a matching journal of the same type."),
		'line_ids' : fields.one2many('account.analytic.line', 'journal_id', 'Lines'),
	}
	_defaults = {
		'active': lambda *a: True,
		'type': lambda *a: 'general',
	}
account_analytic_journal()



# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from osv import osv
from osv import fields
from tools import config

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'max_amount': fields.float('Verify Transaction Above', digits=(16, int(config['price_accuracy'])), help='The max amount that will be used to check payments with account_voucher module, if you left value "0.00" They will never be verified'),
    }
    _defaults = {
        'max_amount': lambda *a: 500,
    }
account_journal()

class AccountVoucher(osv.osv):
    _inherit = 'account.voucher'
    _columns = {
        'state':fields.selection(
            [('draft','Draft'),
             ('proforma','Pro-forma'),
             ('posted','Posted'),
             ('recheck','Waiting for Re-checking'),
             ('cancel','Cancel')
            ], 'State', readonly=True, size=32),
    }
AccountVoucher()

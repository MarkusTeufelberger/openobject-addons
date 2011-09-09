# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#
# Author : Guewen Baconnier (Camptocamp)
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

from osv import osv, fields


class AccountAccount(osv.osv):
    _inherit = 'account.account'

    def _get_level(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        accounts = self.browse(cr, uid, ids, context=context)
        for account in accounts:
            level = 0
            if account.parent_id:
                obj = self.browse(cr, uid, account.parent_id.id)
                level = obj.level + 1
            res[account.id] = level
        return res

    _columns = {
        'centralized': fields.boolean('Centralized', help="If flagged, no details will be displayed in the General Ledger report (the webkit one only), only centralized amounts per period."),
        'level': fields.function(_get_level, string='Level', method=True, store=True, type='integer'),
    }

    _defaults = {
        'centralized': lambda *a: False,
    }

AccountAccount()

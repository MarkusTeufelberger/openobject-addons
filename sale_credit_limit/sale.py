# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai <gdukai@gmail.com>
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

from osv import osv
from tools.translate import _

class sale_order(osv.osv):
    _inherit = "sale.order"

    def check_limit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        so = self.browse(cr, uid, ids[0], context)
        partner = so.partner_id

        due = partner.credit - partner.debit + so.amount_total
        if due > partner.credit_limit:
            if 'lang' not in context:
                user_obj = self.pool.get('res.users')
                lang = user_obj.browse(cr, uid, uid).context_lang
                context.update({'lang': lang})
            msg = _('Cannot confirm Sales Order, credit limit exceeded with %d!\nCheck Partner Accounts or Credit Limit!') \
                % (due - partner.credit_limit)
            raise osv.except_osv(_('Credit Limit Exceeded!'), msg)
            return False
        else:
            return True

sale_order()

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright Camptocamp SA
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
import netsvc
from osv import fields, osv
from tools import config
from tools.translate import _

class sale_order(osv.osv):
    _inherit = "sale.order"

    def test_blocked(self, cr, uid, ids, *args):
        partner_obj = self.pool.get('res.partner') 
        for sale in self.browse(cr, uid, ids, context={}):
            res_partner = partner_obj.search(cr, uid, [('id', '=', sale.partner_id.id)])
            partner = partner_obj.browse(cr, uid, res_partner)[0]
            if partner.block_sales == True:
                return False
        return True

sale_order()
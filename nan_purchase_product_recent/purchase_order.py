# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L.  All Rights Reserved.
#                    http://www.NaN-tic.com
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

from osv import fields
from osv import osv

class purchase_order_line( osv.osv ):
    _inherit = 'purchase.order.line'

    def _recent_product_id(self, cr, uid, ids, field_name, args, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context):
            result[line.id] = line.product_id.id
        return result

    def _set_recent_product_id(self, cr, uid, id, field_name, value, args, context=None):
        return True

    _columns = {
        'recent_product_id': fields.function(_recent_product_id, fnct_inv=_set_recent_product_id, method=True, type='many2one', relation='product.product', string='Recent Product', store=False, help='Here you will only find products the company has ordered to this supplier some time in the past.'),
    }

    def recent_product_id_change(self, cr, uid, ids, pricelist, recent_product, qty=0, uom=False, partner_id=False, date_order=False, fiscal_position=False, context=None):
        if not context:
            context = {}
        result = self.product_id_change(cr, uid, ids, pricelist, recent_product, qty, uom, partner_id, date_order, fiscal_position)
        if not 'value' in result:
            result['value'] = {}
        result['value']['product_id'] = recent_product
        return result

purchase_order_line()


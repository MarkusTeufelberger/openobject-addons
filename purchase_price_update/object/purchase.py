# -*- coding: utf-8 -*-
##############################################################################
#
#    purchase_price_update module for OpenERP, Updates prices in purchase when pricelist is changed
#    Copyright (C) 2010 INVITU SARL (<http://www.invitu.com/>)
#              Sebastien Lange <support@invitu.com>
#
#    This file is a part of purchase_price_update
#
#    purchase_price_update is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    purchase_price_update is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import osv
from osv import fields
import pooler

class purchase_order(osv.osv):
    _inherit="purchase.order"

    def button_dummy(self, cr, uid, ids, context=None):
        '''
        In case pricelist changes, we need to recalculate prices on each line
        '''
        if not context:
            context = {}
        for order in self.browse(cr, uid, ids):
            for oline in order.order_line:
                context.update({ 'uom': oline.product_uom.id }),
                context.update({ 'date': order.date_order }),
                price_unit = self.pool.get('product.pricelist').price_get(cr,uid,
                        [order.pricelist_id.id],
                        oline.product_id.id,
                        oline.product_qty or 1.0,
                        order.partner_id.id,
                        context,
                        )[order.pricelist_id.id]
                self.pool.get('purchase.order.line').write(cr, uid, [oline.id], {'price_unit': price_unit})
        return super(purchase_order,self).button_dummy(cr, uid, ids, context)
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

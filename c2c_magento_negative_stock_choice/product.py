# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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

import netsvc
import paramiko
import time

from osv import fields, osv
from tools.translate import _

class Product(osv.osv):
    " Inherit product in order to add the Negative Stock Magento's behavior"
    _inherit = 'product.product'
    
    _columns = {
                    'magento_backorders': fields.selection(
                            [
                             ('0', 'No Negative Stock Allowed'), 
                             ('1', 'Negative Stock Allowed'), 
                             ('2', 'Negative Stock Allowed (but warn customer)')
                             ],
                             'Magento Backorder', 
                             help="A backorder is for an item that was in stock previously but is temporarily out of stock. \
Choose the Magento comportement here."),
                }
                
    _defaults = {
                    'magento_backorders':lambda *a: '1',
                }                
                
    def export_inventory(self, cr, uid, ids, shop, ctx):
        logger = netsvc.Logger()
        stock_id = self.pool.get('sale.shop').browse(cr, uid, ctx['shop_id']).warehouse_id.lot_stock_id.id
        for product in self.browse(cr, uid, ids):
            if product.magento_exportable and product.magento_sku and product.type != 'service':
                # Changing Stock Availability to "Out of Stock" in Magento
                # if a product has qty lt or equal to 0.
                # And CHANGE the reference quantity to export to Magento
                # For Debonix, we'll use bom_stock value computed into c2c_bom_stock
                bom_stock = self.read(cr, uid, product.id, ['bom_stock'], {'location': stock_id})['bom_stock']
                is_in_stock = int(bom_stock > 0)
                # Normal call to keep
                ctx['conn_obj'].call('product_stock.update', [product.magento_sku, {'qty': bom_stock, 'is_in_stock': is_in_stock, 'use_config_manage_stock':False, 'manage_stock':True, 'backorders':product.magento_backorders}])
                logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Successfully updated stock level at %s for product with SKU %s " %(bom_stock, product.magento_sku))
                
Product()

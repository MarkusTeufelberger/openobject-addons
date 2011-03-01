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
from osv import osv, fields
import netsvc
from tools.translate import _
import string
import time
from  magentoerpconnect import magerp_osv

class SaleShop(magerp_osv.magerp_osv):
    _inherit = "sale.shop"

    _columns = {
        'last_stock_init_date': fields.datetime('Last Stock Initialization Time'),
    }

    def initialize_stock(self,cr,uid,ids,ctx):
        if ctx is None:
            ctx = {}
        logger = netsvc.Logger()
        for shop in self.browse(cr, uid, ids):
            ctx['shop_id'] = shop.id
            ctx['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
            # Call the method to update stock, before giving the right values
            # The goal is to initiate the "manage stock" field in Magento to True
            # Can be remove once bug lp:#667711 is closed
            # Add the products that have no stock.move and type = 'stockable' to initiate the
            # "manage stock" = True in Magento. That allow to not wait the first stock.move before to
            # be able to order them in the website
            #
            # Look for product with no move
            req = "SELECT p.magento_sku as magento_sku, p.magento_backorders as magento_backorders FROM product_product p join product_template t \
                            ON (p.product_tmpl_id = t.id)\
                            WHERE t.type not like 'service' AND\
                            p.magento_sku is not null AND\
                            p.id not in (SELECT distinct(stock_move.product_id) FROM stock_move)\
                            AND p.magento_exportable = true"
            param = ()
            if shop.last_stock_init_date:
                req += " AND (p.write_date > %s OR p.create_date > %s)"
                param = (shop.last_stock_init_date, shop.last_stock_init_date)

            cr.execute(req, param)
            for product in cr.dictfetchall():
                try:
                    ctx['conn_obj'].call('product_stock.update', [product['magento_sku'], {'qty': 0, 'is_in_stock': False, 'use_config_manage_stock':True, 'manage_stock':True, 'backorders':product['magento_backorders']}])
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Successfully updated stock level at %s for product with SKU %s " %(0, product['magento_sku']))
                except:
                    # Pass because we want the maximum product to be updated
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Fail to update stock level at %s for product with SKU %s " %(0, product['magento_sku']))
                    pass
            self.write(cr, uid, shop.id, {'last_stock_init_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True
        
SaleShop()

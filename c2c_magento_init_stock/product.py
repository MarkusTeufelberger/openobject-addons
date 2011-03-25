# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Guewen Baconnier. Copyright Camptocamp SA
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

from  magentoerpconnect import magerp_osv
import netsvc

class product_product(magerp_osv.magerp_osv):
    _inherit = "product.product"

    def magento_init_stock(self, cr, uid, oe_id, conn, context=None):
        product = self.browse(cr, uid, oe_id, context=context)
        logger = netsvc.Logger()
        try:
            # we put "is_in_stock" to true even with 0 stock otherwise we can't order the product
            conn.call('product_stock.update', [product.magento_sku, {'qty': 0,
                                                                     'is_in_stock': True,
                                                                     'use_config_manage_stock':True,
                                                                     'manage_stock':True,
                                                                     'backorders':product.magento_backorders}])
            logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Successfully initialized inventory options on product with SKU %s " % (product.magento_sku,))
        except Exception, e:
            # Pass because we want the maximum product to be updated
            request = self.pool.get('res.request')
            summary = """Product %s : initialization of the inventory options failed on Magento on this product after its creation.
You must set it manually on Magento.
Exception :
%s""" % (product.magento_sku, e)
            request.create(cr, uid,
                           {'name': "Impossible to set the stock options on product %s " % (product.magento_sku,),
                            'act_from': uid,
                            'act_to': uid,
                            'body': summary,
                            })
            cr.commit()
            logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Fail to initialize inventory options for product with SKU %s. \nException: %s" % (product.magento_sku, e))
        return True

    def ext_create(self, cr, uid, data, conn, method, oe_id, context):
        res = super(product_product, self).ext_create(cr, uid, data, conn, method, oe_id, context)
        # initialize the inventories options on the magento product
        self.magento_init_stock(cr, uid, oe_id, conn, context)
        return res

product_product()
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

import netsvc

from osv import osv, fields
from base_external_referentials import external_osv
from tools.translate import _


class SaleShop(external_osv.external_osv):
    """Override the sale.shop object to modify the behavior of the shipping export.
    In the base external referential module, they are exported in a random order,
    and here they are exported in their order. """
    _inherit = "sale.shop"
    
    def export_shipping(self, cr, uid, ids, ctx):
        """Export shipping in their order from first to last. Based on the backorder id.
        Only the SQL query is modified on that function"""
        logger = netsvc.Logger()
        for shop in self.browse(cr, uid, ids):
            ctx['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
        
            cr.execute("""
                select stock_picking.id, sale_order.id, count(pickings.id), stock_picking.backorder_id from stock_picking
                left join sale_order on sale_order.id = stock_picking.sale_id
                left join stock_picking as pickings on sale_order.id = pickings.sale_id
                left join ir_model_data on stock_picking.id = ir_model_data.res_id and ir_model_data.model='stock.picking'
                where shop_id = %s and ir_model_data.res_id ISNULL and stock_picking.state = 'done'
                Group By stock_picking.id, sale_order.id, stock_picking.backorder_id order by sale_order.id asc, COALESCE(stock_picking.backorder_id, NULL, 0) asc;
                """, (shop.id,))
            results = cr.fetchall()
            for result in results:
                if result[2] == 1:
                    picking_type = 'complete'
                else:
                    picking_type = 'partial'
                
                ext_shipping_id = self.pool.get('stock.picking').create_ext_shipping(cr, uid, result[0], picking_type, shop.referential_id.id, ctx)

                if ext_shipping_id:
                    ir_model_data_vals = {
                        'name': "stock_picking_" + str(ext_shipping_id),
                        'model': "stock.picking",
                        'res_id': result[0],
                        'external_referential_id': shop.referential_id.id,
                        'module': 'extref.' + shop.referential_id.name
                      }
                    self.pool.get('ir.model.data').create(cr, uid, ir_model_data_vals)
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Successfully creating shipping with OpenERP id %s and ext id %s in external sale system" % (result[0], ext_shipping_id))
    
    
SaleShop()

class SaleOrder(osv.osv):
    """Override the sale.order to delete the components of a "Pack" product when they are
    in the order. We have to do that because Magento send the pack and his components in the sale order.
    We only delete the components with a 0.0 price because one may order a component independently.
    """
    
    _inherit = "sale.order"    
    
    def create(self, cr, uid, vals, context={}):
        """ Creation of the sale order. Delete components of a BoM with 0.0 price."""
        product_obj = self.pool.get('product.product')
        
        if vals.get('order_line', False):
            for array_line in vals['order_line'][:]: # iterate over a copy of order lines to not delete lines on the original during the loop
                line = array_line[2] # key 2 because vals['order_line'] = [0, 0, {values}]
                product_id = line['product_id']
                # search if product is a BoM if it is, loop on other products
                # to search for his components to drop
                product = product_obj.browse(cr, uid, product_id)
                
                if not product.bom_ids:
                    continue
                
                # compute the list of products components of the BoM
                bom_prod_ids = []
                for bom in product.bom_ids:
                    [bom_prod_ids.append(bom_line.product_id.id) for bom_line in bom.bom_lines]
                
                for other_array_line in vals['order_line'][:]: 
                    other_line = other_array_line[2]
                    if other_line['product_id'] == product_id:
                        continue
                    
                    # remove the lines of the bom where the price is 0.0
                    # because we don't want to remove it if it is ordered alone
                    if other_line['product_id'] in bom_prod_ids and not other_line['price_unit']:
                        vals['order_line'].remove(other_array_line)

        return super(SaleOrder, self).create(cr, uid, vals, context=context)
    
SaleOrder()

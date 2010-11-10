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

from osv import fields, osv
from tools.translate import _
from base_external_referentials import external_osv
import time
import netsvc


                    

class ProductRelation(external_osv.external_osv):
    _name = 'magento.product.relation'
    _rec_name = 'related_product'
    _columns = { 
                 'product_id':fields.many2one('product.product', 'Source product', required=True), 
                 'related_product':fields.many2one('product.product', 'Related product',required=True),
                 'type':fields.selection([('cross_sell','Cross Sell'), ('up_sell','Up sell'), ('related','Related')],'Type',required=True)
                 }
                 
    def ext_export(self, cursor, uid, ids, external_referential_ids=None, defaults=None, context=None):
        raise Exception('Not implemented Yet')
        
    def export_plink_from_product(self, cursor, uid, prod_id, shop_id, context=None):
        if not context or not context.get('conn_obj',False):
            raise Exception('No connexion object in context')
        prod_br = self.pool.get('product.product').browse(cursor, uid, prod_id)
        if not prod_br.magerp_cross_selling :
            return
        links = []
        for type in ('related','cross_sell','up_sell'):
            links = context['conn_obj'].call('product_link.list', [type, prod_br.magento_sku])
            for exisiting in links:
                context['conn_obj'].call('product_link.remove', [type, prod_br.magento_sku, exisiting['sku']])
        for link in prod_br.magerp_cross_selling :
            valuedict = {}
            for value in link.value_ids :
                valuedict[value.name] = value.value
            if link.related_product.magento_sku :
                context['conn_obj'].call('catalog_product_link.assign', 
                                            [
                                                link.type, 
                                                prod_br.magento_sku, 
                                                link.related_product.magento_sku, 
                                                valuedict
                                            ]
                                        )
        self.pool.get('sale.shop').write(
            cursor, 
            uid, 
            shop_id, 
            {'last_product_link_export': time.strftime('%Y-%m-%d %H:%M:%S')}
        )
    
ProductRelation()

class ProductRelationValue(osv.osv):
    _name = 'magento.product.relation.value'
    _columns = { 
                'name':fields.char('name', size=128, required=True),
                'value':fields.char('value', size=128, required=True),
                'relation_id':fields.many2one('magento.product.relation', 'Magento Values')
                }

ProductRelationValue()

class ProductRelationRel(osv.osv):
    _inherit = 'magento.product.relation'
    _columns = { 
                 'value_ids': fields.one2many(
                          'magento.product.relation.value', 
                          'relation_id', 
                          'Magento Values',
                          required=False,
                          help='Relation attributes like qty, order, ect.',
                          ondelete='cascade'
                        ),                 
                }
ProductRelationRel()



class Product(osv.osv):
    " Inherit product in orer to manage equivalances"
    _inherit = 'product.product'

    _columns = {
                    ##We choose this name in order to be sure that it will not be in attribute set. 
                   'magerp_cross_selling':fields.one2many(
                          'magento.product.relation', 
                          'product_id', 
                          'Cross selling relation',
                          required=False,
                        ),
                         
                    # 'magerp_related_selling':fields.one2many(
                    #       'magento.product.relation', 
                    #       'product_id', 
                    #       'Related selling relation',
                    #       required=False,
                    #     ),
                    #      
                    # 'magerp_up_selling':fields.one2many(
                    #       'magento.product.relation', 
                    #       'product_id', 
                    #       'up selling relation',
                    #       required=False,
                    #     ),
                }
                

Product()

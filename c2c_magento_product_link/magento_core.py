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
from  magentoerpconnect import magerp_osv
from base_external_referentials import external_osv
import tools


DEBUG = True
TIMEOUT = 2

class ExternalRreferential(magerp_osv.magerp_osv):
    #This class stores instances of magento to which the ERP will connect, so you can connect OpenERP to multiple Magento installations (eg different Magento databases)
    _inherit = "external.referential"
    
    def import_link(self, cr, uid, ids, ctx):
        types = ['cross_sell','up_sell','related'] #I know it is a little nasty #Mark to improve
        instances = self.browse(cr, uid, ids, ctx)
        prod_obj =  self.pool.get('product.product')
        link_obj = self.pool.get('magento.product.relation')
        for inst in instances:
            attr_conn = self.external_connection(cr, uid, inst, DEBUG)
            products_ids = prod_obj.search(cr, uid, [('magento_exportable', '=', True)])
            for product in prod_obj.browse(cr, uid, products_ids):
                res = []
                for type in types :
                    tmp = attr_conn.call('product_link.list', [type, product.magento_sku])
                    for line in tmp :
                        line['type'] = type
                    res += tmp
                if res :
                    l_ids = link_obj.search(cr, uid, [('product_id', '=', product.id)]) 
                    if l_ids :
                        link_obj.unlink(cr, uid, l_ids)
                        
                    for link in res :
                        rel_id = prod_obj.extid_to_oeid(cr, uid, product.id, inst.id)
                        link_obj.create(cr, uid, {'product_id':product.id,
                                                  'type':link.get('type','related'),
                                                  'related_product':rel_id
                                                }
                                        )
                                           
        return True

    
ExternalRreferential()
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Joël Grand-Guillaume and Guewen Baconnier. Copyright Camptocamp SA
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
import time

from osv import fields, osv
from tools.translate import _

class Product(osv.osv):
    " Inherit product to manage components on products"
    _inherit = 'product.product'

    def _get_components(self, cr, uid, ids, field_names=None, arg=False, context=None):
        if context is None:
            context = {}
        if field_names is None:
            field_names = []   
            
        bom_obj = self.pool.get('mrp.bom')            
        res = {}
        
        # Initialize with no components        
        for id in ids:
            res[id] = False

        # Take all concerned product which have a BoM
        bom_ids = bom_obj.search(cr, uid, [('product_id', 'in', ids),
                                           ('bom_id', '=', False)])        

        for bom in bom_obj.browse(cr, uid, bom_ids):
            components = []
            for line in bom.bom_lines:
                 components.append(line.product_id.magento_sku)
            res[bom.product_id.id] =  ','.join(map(str, components))
            
        return res
    
    def _get_concerned_boms(self, cr, uid, ids, context=None):
        if not context:
            context = {}        
        bom_ids = {}
        product_ids = []
        bom_obj = self.pool.get('mrp.bom')
        bom_ids = bom_obj.search(cr,uid,[('product_id', 'in', ids)])
        
        for bom in bom_obj.browse(cr, uid, ids):
            product_ids.append(bom.product_id.id)
        if product_ids:
            cr.execute("update product_product set write_date = now() where id in (%s)"%(','.join(map(str,product_ids))))
        return product_ids

    _columns = {'components_lists': 
                    fields.function(
                        _get_components,
                        method=True,
                        type='char',
                        size=256, 
                        string='Components list (SKU)',
                        help="List of components of this product taken from the BoM (separation with ','). Only one level deep, not recursive",                    
                        store = {
                            'product.product': (lambda self, cr, uid, ids, c={}: ids, ['bom_ids'], 10),
                            'mrp.bom': (_get_concerned_boms, ['bom_lines'], 10),
                        }
                        ),
                }
                
Product()

class MrpBom(osv.osv):
    "Inherit mrp.bom to reset the components infos on product when a BoM is deleted"
    _inherit = "mrp.bom"
    
    def unlink(self, cr, uid, ids, context=None):
        for bom in self.pool.get('mrp.bom').browse(cr, uid, ids):
            if bom.product_id.components_lists:
                self.pool.get('product.product').write(cr, uid, bom.product_id.id, {'components_lists': False,})
        
        return super(MrpBom, self).unlink(cr, uid, ids, context)
    
MrpBom()    


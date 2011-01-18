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
import time

from osv import fields, osv
from tools.translate import _

class Product(osv.osv):
    " Inherit product to manage set and packs on products "
    _inherit = 'product.product'

    def _get_type_and_components(self, cr, uid, ids, field_names=None, arg=False, context={}):
        bom_obj=self.pool.get('mrp.bom')
        if not field_names:
            field_names=[]
        res = {}
        # TODO: search the attribute id by it's code !
        # 256 is the ID for the attribute zdbx_default_set_or_pack & 0,1,2 the value
        simple_product_id = self.pool.get('magerp.product_attribute_options').search(cr,uid,[('attribute_id','=',256),('value','=',0)])
        set_product_id = self.pool.get('magerp.product_attribute_options').search(cr,uid,[('attribute_id','=',256),('value','=',1)])
        pack_product_id = self.pool.get('magerp.product_attribute_options').search(cr,uid,[('attribute_id','=',256),('value','=',2)])
        att_values_ids = {'0':simple_product_id,'1':set_product_id,'2':pack_product_id}
        # Initialize with simple product, with no components
        for id in ids:
            res[id]={}.fromkeys(field_names)
            res[id]['components_lists'] = ''
            res[id]['simple_set_or_pack'] = '0'
        # Take all concerned product with BoM
        bom_ids = bom_obj.search(cr,uid,[('product_id','in',ids),('bom_id','=',False)])
        boms = bom_obj.browse(cr,uid,bom_ids)
        for bom in boms:
            components = []
            for line in bom.bom_lines:
                 components.append(line.product_id.magento_sku)
            res[bom.product_id.id]['components_lists'] =  ','.join(map(str,components))

            if bom.type == 'normal':
                res[bom.product_id.id]['simple_set_or_pack'] = '1'
            elif bom.type == 'phantom':
                res[bom.product_id.id]['simple_set_or_pack'] = '2'
            # Update related attrs
            # TODO : Remove, this was to handle this without the x_magerp_zdbx_default_set_pack attrs
            # in OpenERP
            tmp=att_values_ids[res[bom.product_id.id]['simple_set_or_pack']]
            if type(tmp) == list:
                tmp=tmp[0]
            self.write(cr,uid,bom.product_id.id,{'x_magerp_zdbx_default_sku_coffrets':res[bom.product_id.id]['components_lists'],'x_magerp_zdbx_default_set_pack':tmp})
        return res
    
    def _get_concerned_boms(self, cr, uid, ids, context={}):
        bom_ids = {}
        product_ids=[]
        bom_obj=self.pool.get('mrp.bom')
        bom_ids=bom_obj.search(cr,uid,[('product_id','in',ids)])
        
        for bom in bom_obj.browse(cr, uid, ids):
            product_ids.append(bom.product_id.id)
        if product_ids:
            cr.execute("update product_product set write_date = now() where id in (%s)"%(','.join(map(str,product_ids))))
        return product_ids

    _columns = {'simple_set_or_pack': fields.function(_get_type_and_components, method='simple_set_or_pack', type='selection', string='Manage product type as (value)',
                            selection=[('0','Simple product with no BoM'),('1','Set Product (Normal BoM)'),('2','Pack Product (Phantom BoM)')],
                            help="Function field linked with the 'zdbx_default_set_pack' magento attribute. How to deal with the product, store :\
0 for simple (no BoM), 1 for set (Normal BoM), 2 for pack (Phantom BoM).", 
                            multi=True,
                            store = {
                                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['bom_ids'], 10),
                                'mrp.bom': (_get_concerned_boms, ['type', 'bom_lines'], 10),
                            }),
                'components_lists': fields.function(_get_type_and_components, method='simple_set_or_pack', type='char', size=256, string='Components list',
                            help="List of components of this product taken from the BoM (separation with ';'). Only one level deep, not recursive",
                            multi=True,
                            store = {
                                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['bom_ids'], 10),
                                'mrp.bom': (_get_concerned_boms, ['type', 'bom_lines'], 10),
                            }),
                }
                
Product()


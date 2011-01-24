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
    " Inherit product to manage set and packs on products "
    _inherit = 'product.product'

    def _get_type(self, cr, uid, ids, field_names=None, arg=False, context=None):
        if context is None:
            context = {}
        if field_names is None:
            field_names = []           
        bom_obj = self.pool.get('mrp.bom')
        res = {}
        
        # Initialize with simple product
        for id in ids:
            res[id] = False
        
        # Take all concerned product which have a BoM
        bom_ids = bom_obj.search(cr, uid, [('product_id', 'in', ids),
                                           ('bom_id', '=', False)])

        for bom in bom_obj.browse(cr, uid, bom_ids):                                           
            if bom.type == 'normal':
                res[bom.product_id.id] = 'set'
            elif bom.type == 'phantom':
                res[bom.product_id.id] = 'pack'
        
        return res

    def _get_store_boms(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        bom_ids = product_obj._get_concerned_boms(cr, uid, ids, context)
        return bom_ids

    _columns = {'simple_set_or_pack': 
                    fields.function(
                        _get_type, 
                        method=True,
                        type='selection',
                        string='Manage product type as (value)',
                        selection=[(False, 'Simple product with no BoM'),
                                   ('set','Set Product (Normal BoM)'),
                                   ('pack','Pack Product (Phantom BoM)')],
                        help="Function field linked with a magento attribute. Used on Magento to handle the products.", 
                        store={
                            'product.product': (lambda self, cr, uid, ids, c={}: ids, ['bom_ids'], 10),
                            'mrp.bom': (_get_store_boms, ['type'], 10),
                        }),                 
                }
                
Product()

class MrpBom(osv.osv):
    "Inherit mrp.bom to reset the pack and components infos on product when a BoM is deleted"
    _inherit = "mrp.bom"
    
    def unlink(self, cr, uid, ids, context=None):
        for bom in self.pool.get('mrp.bom').browse(cr, uid, ids):
            if bom.product_id.simple_set_or_pack:
                self.pool.get('product.product').write(cr, uid, bom.product_id.id,{'simple_set_or_pack': False,})
        
        return super(MrpBom, self).unlink(cr, uid, ids, context)
    
MrpBom()    

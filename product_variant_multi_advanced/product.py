# -*- encoding: utf-8 -*-
##############################################################################
#
#    Model module for OpenERP
#    Copyright (C) 2010 Sébastien BEAU <sebastien.beau@akretion.comr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
# Lib required to print logs
import netsvc
# Lib to translate error messages
from tools.translate import _

class product_product(osv.osv):
    _inherit = "product.product"
    
    def _get_products_from_product(self, cr, uid, ids, context={}):
        return super(product_product, self.pool.get('product.product'))._get_products_from_product(cr, uid, ids, context=context)
    
    def _get_products_from_product_template(self, cr, uid, ids, context={}):
        return super(product_product, self.pool.get('product.product'))._get_products_from_product_template(cr, uid, ids, context=context)
        
    def _build_product_name(self, cr, uid, ids, name, arg, context={}):
        res={}
        for product in self.browse(cr, uid, ids, context=context): #['id', 'product_tmpl_id', 'variants'],
            res[product.id] = (product.product_tmpl_id.name or '' )+ ' ' + (product.variants or '')
        return res
    
    _columns = {
        'name' : fields.function(_build_product_name, method=True, type='char', size=128, string='Name', readonly=True,
            store={
                'product.product': (_get_products_from_product, ['variants'], 15),
                'product.template': (_get_products_from_product_template, ['name'], 15),
            }),
    }
product_product()
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Model module for OpenERP
#    Copyright (C) 2010 Sébastien BEAU <sebastien.beau@akretion.com>
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


def get_vals_to_write(vals, fields):
    vals_to_write = {}
    for field in fields:
        if field in vals.keys():
            vals_to_write[field] = vals[field]
    return vals_to_write

#Add your duplicated fields here
duplicated_fields = ['description_sale']

class product_template(osv.osv):
    _inherit = "product.template"
    
    def button_generate_product_sale_description(self, cr, uid, ids, context=None):
        product_ids = self.get_products_from_product_template(cr, uid, ids, context=context)
        self.pool.get('product.product').build_product_sale_description(cr, uid, product_ids, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context={}

        if not context.get('iamthechild', False) and not context.get('is_multi_variants', False) and not vals.get('is_multi_variants', False):
            vals_to_write = get_vals_to_write(vals, duplicated_fields)

            if vals_to_write:
                obj_product = self.pool.get('product.product')
                ctx = context.copy()
                ctx['iamthechild'] = True
                for product_tmpl in self.read(cr, uid, ids, ['is_multi_variants', 'variant_ids'], context=context):
                    if not product_tmpl['is_multi_variants']:
                        obj_product.write(cr, uid, [product_tmpl['variant_ids'][0]], vals_to_write, context=ctx)

        return super(product_template, self).write(cr, uid, ids, vals, context=context)
    
product_template()

class product_product(osv.osv):
    _inherit = "product.product"

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context={}

        if not context.get('iamthechild', False) and not context.get('is_multi_variants', False) and not vals.get('is_multi_variants', False):
            vals_to_write = get_vals_to_write(vals, duplicated_fields)

            if vals_to_write:
                obj_tmpl = self.pool.get('product.template')
                ctx = context.copy()
                ctx['iamthechild'] = True
                for product in self.read(cr, uid, ids, ['is_multi_variants', 'product_tmpl_id'], context=context):
                    if not product['is_multi_variants']:
                        obj_tmpl.write(cr, uid, [product['product_tmpl_id'][0]], vals_to_write, context=ctx)

        return super(product_product, self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        #TAKE CARE for inherits objects openerp will create firstly the product_template and after the product_product
        # and so the duplicated fields will be on the product_template and not on the product_product
        ids = super(product_product, self).create(cr, uid, vals.copy(), context=context) #take care to use vals.copy() if not the vals will be changed by calling the super method
        ####### write the value in the product_product
        ctx = context.copy()
        ctx['iamthechild'] = True
        vals_to_write = get_vals_to_write(vals, ['name']+duplicated_fields)
        if vals_to_write:
            self.write(cr, uid, ids, vals_to_write, context=ctx)
        return ids


    def _get_products_from_product(self, cr, uid, ids, context=None):
        #for a strange reason calling super with self doesn't work. maybe an orm bug
        return super(product_product, self.pool.get('product.product'))._get_products_from_product(cr, uid, ids, context=context)
    
    def _get_products_from_product_template(self, cr, uid, ids, context=None):
        #for a strange reason calling super with self doesn't work. maybe an orm bug
        return super(product_product, self.pool.get('product.product'))._get_products_from_product_template(cr, uid, ids, context=context)
        
    def _build_product_name(self, cr, uid, ids, name, arg, context=None):
        res={}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = (product.product_tmpl_id.name or '' )+ ' ' + (product.variants or '')
        return res
    
    def _inv_set_name(self, cr, uid, ids, name, value, arg, context=None):
        print '_inv_set_name', value, context
        if isinstance(ids, (int, long)):
            ids = [ids]
        obj_tmpl = self.pool.get('product.template')
        for product in self.read(cr, uid, ids, ['product_tmpl_id'], context=context):
            obj_tmpl.write(cr, uid, product['product_tmpl_id'][0], {'name' : value}, context=context)
        return True

    def build_product_sale_description(self, cr, uid, ids, context=None):
        if not context:
            context={}
        context['is_multi_variants']=True
        obj_lang=self.pool.get('res.lang')
        lang_ids = obj_lang.search(cr, uid, [], context=context)
        lang_code = [x['code'] for x in obj_lang.read(cr, uid, lang_ids, ['code'], context=context)]
        for code in lang_code:
            context['lang'] = code
            for product in self.browse(cr, uid, ids, context=context):
                description = self.parse(cr, uid, product, product.product_tmpl_id.description_sale, context=context)
                self.write(cr, uid, product.id, {'description_sale':description}, context=context)
        return True
    
    _columns = {
        'name' : fields.function(_build_product_name, fnct_inv=_inv_set_name, method=True, type='char', size=128, string='Name', translate=True,
            store={
                'product.product': (_get_products_from_product, ['variants'], 15),
                'product.template': (_get_products_from_product_template, ['name', 'variant_model_name', 'variant_model_name_separator'], 15),
            }),
            
        'description_sale': fields.text('Sale Description',translate=True),
    }
product_product()



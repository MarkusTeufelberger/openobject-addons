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
# Lib to eval python code with security
from tools.safe_eval import safe_eval


class product_template(osv.osv):
    _inherit = "product.template"
    
    def button_generate_product_sale_description(self, cr, uid, ids, context=None):
        product_ids = self.get_products_from_product_template(cr, uid, ids, context=context)
        self.pool.get('product.product').build_product_sale_description(cr, uid, product_ids, context=context) 
    
product_template()

class product_product(osv.osv):
    _inherit = "product.product"
    
    def parse(self, cr, uid, o, text, context=None):
        vals = text.split('[_')
        description = ''
        for val in vals:
            if ']' in val:
                sub_val = val.split('_]')
                description += str(safe_eval(sub_val[0], {'o' :o, 'context':context})) + sub_val[1]
            else:
                description += val
        return description
        
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
    
    def build_product_sale_description(self, cr, uid, ids, context=None):
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
        'name' : fields.function(_build_product_name, method=True, type='char', size=128, string='Name', readonly=True,
            store={
                'product.product': (_get_products_from_product, ['variants'], 15),
                'product.template': (_get_products_from_product_template, ['name'], 15),
            }),
            
        'description_sale': fields.text('Sale Description',translate=True, readonly=True),
    }
product_product()



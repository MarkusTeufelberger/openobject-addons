# -*- coding: utf-8 -*-
##############################################################################
#
#    product_tax_category module for OpenERP
#    Copyright (C) 2009 SYLEAM (<http://www.syleam.fr>) Christophe CHAUVET
#
#    This file is a part of product_tax_category
#
#    product_tax_category is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    product_tax_category is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
from tools.translate import _

class product_category(osv.osv):
    _inherit = 'product.category'

    _columns = {
        'sale_taxes_ids': fields.many2many('account.tax', 'product_cat_tax_cust_rel',
            'cat_id', 'tax_id', 'Sales Taxes',
            domain=[('parent_id','=',False),('type_tax_use','in',['sale','all'])]),
        'purchase_taxes_ids': fields.many2many('account.tax', 'product_cat_tax_supp_rel',
            'cat_id', 'tax_id', 'Purchase Taxes',
            domain=[('parent_id', '=', False),('type_tax_use','in',['purchase','all'])]),
        'uom_id': fields.many2one('product.uom', 'Default UoM'),
        'uom_po_id': fields.many2one('product.uom', 'Purchase UoM'),
        'uos_id': fields.many2one('product.uom', 'Unit of Sale', help="See product definition"),
        'uos_coeff': fields.float('UOM -> UOS Coeff', digits=(16,4), help="See product definition"),
    }

product_category()

class product_product(osv.osv):
    _inherit = 'product.product'

    def onchange_category(self, cr, uid, ids, category, context=None):
        """
        When category change, we search:
        * Taxes (sale and purchase)
        * UOM
        * Product Type
        """
        if not context: context = {}

        res = {}
        warn = False
        if not category:
            res['categ_id'] = res['uom_id'] = res['uom_po_id'] = False
            res['supplier_taxes_id'] = []
            res['taxes_id'] = []
        else:
            # Search default value on this category
            categ = self.pool.get('product.category').read(cr, uid, [category])[0]
            res['categ_id'] =  category
            if categ['sale_taxes_ids']:
                res['taxes_id'] = categ['sale_taxes_ids']
            if categ['purchase_taxes_ids']:
                res['supplier_taxes_id'] = categ['purchase_taxes_ids']
            if categ['uom_id']:
                res['uom_id'] = categ['uom_id']
            if categ['uom_po_id']:
                res['uom_po_id'] = categ['uom_po_id']
            if categ['uos_id']:
                res['uos_id'] = categ['uos_id']
                res['uos_coeff'] = categ['uos_coeff']
            if ids:
                warn = {}
                warn['title'] = _('Caution')
                warn['message'] = _("""The product category have been changed, thanks to control
* Sales and Purchases Taxes
* Unit sales and stock
* The price with return unit""")
        return {'value': res, 'warning': warn}

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

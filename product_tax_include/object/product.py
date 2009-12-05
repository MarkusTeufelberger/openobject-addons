# -*- coding: utf-8 -*-
##############################################################################
#
#    product_tax_include module for OpenERP, Add new field for tax include in product
#    Copyright (C) 2009 SYLEAM Info Services (<http://www.Syleam.fr/>) Sebastien LANGE
#
#    This file is a part of product_tax_include
#
#    product_tax_include is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    product_tax_include is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv
from tools import config

from tools.translate import _

class product_template(osv.osv):
    _inherit = 'product.template'

    def _price_unit_tax(self, cr, uid, ids, field_name, arg, context=None):
        """This method calcul the sale price with/without taxes included depending on company configuration"""
        if not context: context = {}
        res = {}
        tax_obj = self.pool.get('account.tax')
        users_obj = self.pool.get('res.users')
        user = users_obj.browse(cr, uid, uid, context)
        prices_tax_include = user.company_id.product_prices_tax_include
        cur_obj = self.pool.get('res.currency')
        cur = user.company_id.partner_id.property_product_pricelist.currency_id

        for product in self.browse(cr, uid, ids):
            val = 0.0
            if prices_tax_include:
                val = reduce(lambda x, y: x+cur_obj.round(cr, uid, cur, y['amount']),
                    tax_obj.compute_inv(cr, uid, product.taxes_id,
                        product.list_price, 1),
                        val)
                res[product.id] = cur_obj.round(cr, uid, cur, (product.list_price - val))
            else:
                val = reduce(lambda x, y: x+cur_obj.round(cr, uid, cur, y['amount']),
                    tax_obj.compute(cr, uid, product.taxes_id,
                        product.list_price, 1),
                        val)
                res[product.id] = cur_obj.round(cr, uid, cur, (product.list_price + val))
        return res

    _columns = {
            'price_unit_tax' : fields.function(_price_unit_tax,
                                method=True,
                                string='Sale price with taxes included or excluded',
                                store=False,
                                type='float',
                                digits=(16, int(config['price_accuracy'])),
                                help="Price calculated with taxes included or excluded, depend of the configuration in company configuration"),
    }

product_template()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

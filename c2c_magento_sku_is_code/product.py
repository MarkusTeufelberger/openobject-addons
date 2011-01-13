# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Guewen Baconnier. Copyright Camptocamp SA
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
from tools.translate import _

class Product(osv.osv):
    """Inherit product to use the default code as the Magento SKU. Copy the default code into the magento_sku field."""
    _inherit = 'product.product'

    _columns = {
                'magento_sku':fields.char('Magento SKU', size=64, readonly=True),
                }

    _sql_constraints = [
        ('code_uniq', 'unique(default_code)', 'The code must be unique')
    ]

    def _get_sku(self, cr, uid, vals, context=None):
        # check if code doesn't contain "," (some magento's attributes contain list of skus delimited by ",")
        if ',' in vals['default_code']:
            raise osv.except_osv(_('Error!'), _('The code must not contain commas (,) !'))

        return vals['default_code']

    def create(self, cr, uid, vals, context=None):
        if vals.get('default_code', False):
            vals['magento_sku'] = self._get_sku(cr, uid, vals, context)

        return super(Product, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}

        if vals.get('default_code', False):
            modify = True
            sale_obj = self.pool.get('sale.shop')
            shops_ids = sale_obj.search(cr, uid, [('magento_shop', '=', True),])

            # check if product exists on Magento and not modify the sku if it is
            for shop in sale_obj.browse(cr, uid, shops_ids, context):
                for product_id in ids:
                    mgn_product = self.oeid_to_extid(cr, uid, product_id, shop.referential_id.id)
                    if mgn_product:
                        modify = False
                        break
            if modify:
                vals['magento_sku'] = self._get_sku(cr, uid, vals, context)

        return super(Product, self).write(cr, uid, ids, vals, context)


    def copy(self, cr, uid, id, default=None, context=None):
        if not context:
            context = {}
        if not default:
            default = {}

        default['magento_sku'] = False
        default['default_code'] = False

        return super(Product, self).copy(cr, uid, id, default=default, context=context)

Product()

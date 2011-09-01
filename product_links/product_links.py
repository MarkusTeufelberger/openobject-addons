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

from osv import fields, osv


class product_link(osv.osv):
    """ Product links between products like cross-sell, up-sell, related"""
    _name = 'product.link'
    _description = "Product links"
    _rec_name = 'linked_product_id'

    def get_link_type_selection(self, cr, uid, context=None):
        # selection can be inherited
        return [('cross_sell', 'Cross-Sell'), ('up_sell', 'Up-Sell'), ('related', 'Related')]

    _columns = {
        'product_id': fields.many2one('product.product', 'Source product', required=True),
        'linked_product_id': fields.many2one('product.product', 'Linked product', required=True),
        'type': fields.selection(get_link_type_selection, 'Link type', required=True),
    }

    def init(self, cr):
        # migration from c2c_magento_product_link
        cr.execute('select * from ir_module_module where name=%s and state in %s',
            ('c2c_magento_product_link', tuple(['installed', 'to upgrade'])))
        if cr.fetchone():
            cr.execute("""
            insert into product_link (create_uid, create_date, type, product_id, linked_product_id)
            select 1 as uid, now(), type, product_id, related_product from
              (select type, product_id, related_product from magento_product_relation
               except
               select type, product_id, linked_product_id from product_link) diff;""")
        return True

product_link()


class product(osv.osv):
    """Inherit product in order to manage product links"""
    _inherit = 'product.product'

    _columns = {
        'product_link_ids': fields.one2many(
            'product.link',
            'product_id',
            'Product links',
            required=False,
            ),
        }

product()

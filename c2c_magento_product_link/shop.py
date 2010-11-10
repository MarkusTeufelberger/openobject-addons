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

from osv import fields, osv
from tools.translate import _
from base_external_referentials import external_osv


class Shop(external_osv.external_osv):
    _inherit = "sale.shop"

    _columns = {
                  'last_product_link_export' : fields.datetime('Last Product link export Time'),

                }
                
    def export_link(self, cr, uid, ids, ctx):
        for shop in self.browse(cr, uid, ids):
            ctx['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
            pids = [x.id for x in shop.exportable_product_ids]
            pids = self.pool.get('product.product').search(cr, uid, [('id', 'in', pids), ('magento_exportable', '=', True)])
            for prod_id in pids:
                self.pool.get('magento.product.relation').export_plink_from_product(cr, uid, prod_id, shop.id, ctx)

            #self.export_categories(cr, uid, shop, ctx)
        return False
Shop()


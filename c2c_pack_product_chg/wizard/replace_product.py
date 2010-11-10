# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume. Copyright Camptocamp SA
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

class replace_product(osv.osv_memory):
    _name = "replace.product"
    _description = "Replace Product"
    _columns = {
        'product_id': fields.many2one('product.product', 'Replace by product', required=True, help="Choose which products will replace the original one."),
    }

    def replace(self, cr, uid, data, context=None):
          rec_id = context and context.get('active_ids', False)
          move_obj = self.pool.get('stock.move')
          partner_obj = self.pool.get('res.partner')
          ctx ={}
          prod_id = self.browse(cr, uid, data[0], context).product_id or False
          for move in move_obj.browse(cr, uid, rec_id):
              if move.state in ['done','cancel']:
                    raise osv.except_osv(_('Error!'),  _('You cannot replace a product on a delivred or canceled move !'))
              if not prod_id:
                  raise osv.except_osv(_('Error!'),  _('You must choose a product !'))
              if move.picking_id.address_id.partner_id:
                    lang = partner_obj.browse(cr, uid, move.picking_id.address_id.partner_id.id).lang
                    ctx = {'lang': lang}              
              line_name = self.pool.get('product.product').name_get(cr, uid, [prod_id.id], context=ctx)[0][1]
              # Make the replacement of the product. Store the old one !
              move_obj.write(cr, uid, [move.id], {
                      'product_id': prod_id.id,
                      'old_product_id': move.product_id.id,
                      'name' : line_name[:64],
                  })
          return {}

replace_product()


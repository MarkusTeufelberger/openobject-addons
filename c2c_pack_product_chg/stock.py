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
import time
import netsvc

class stock_move(osv.osv):
    _inherit = "stock.move"


    _columns = {
        'old_product_id': fields.many2one('product.product', 'Ordred Product', readonly=True, help="The field will be fullfill by the system with the customer ordred product when you choose to replace it during the packing operation."),
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True,readonly=True, states={'draft':[('readonly',False)]}),
    }

stock_move()

class stock_picking(osv.osv):
    _inherit = "stock.picking"

    BASE_TEXT_FOR_OLD_PRD_REPLACE = _("""
    --
    This product replace partially or completely the ordred product : 
    """)

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        '''Call after the creation of the invoice line. We add a comment to let the customer know
        about the replacment of the product.'''
        res=super(stock_picking,self)._invoice_line_hook(cr,uid,move_line,invoice_line_id)
        if move_line.old_product_id :
            partner_obj = self.pool.get('res.partner')
            inv_line_obj = self.pool.get('account.invoice.line')
            prod_obj = self.pool.get('product.product')
            ctx ={}
            if move_line.picking_id.address_id:
                    lang = partner_obj.browse(cr, uid, move_line.picking_id.address_id.partner_id.id).lang
                    ctx = {'lang': lang}
            for inv_line in inv_line_obj.browse(cr,uid,[invoice_line_id]):
                current_note = inv_line.note or ''
                product_note = prod_obj.name_get(cr, uid, [move_line.old_product_id.id], context=ctx)[0][1]
                new_note = current_note + self.BASE_TEXT_FOR_OLD_PRD_REPLACE + product_note
                inv_line_obj.write(cr, uid, inv_line.id, {'note': new_note})
        
        return res
        
        

stock_picking()
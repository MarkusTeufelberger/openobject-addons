# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2009 Àngel Àlvarez - NaN  (http://www.nan-tic.com) All Rights Reserved.
#
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import datetime

from osv import osv
from osv import fields
from tools.translate import _
import netsvc

class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    def _change_prod_qty(self, cr, uid, id ,quantity, context):

        prod_obj = self.pool.get('mrp.production')
        prod = prod_obj.browse(cr, uid, id , context=context)
        prod_obj.write(cr, uid, prod.id, {'product_qty' : quantity })
        prod_obj.action_compute(cr, uid, [prod.id])

        move_lines_obj = self.pool.get('stock.move')
        for move in prod.move_lines:
            bom_point = prod.bom_id
            bom_id = prod.bom_id.id
            if not bom_point:
                bom_id = self.pool.get('mrp.bom')._bom_find(cr, uid, prod.product_id.id, prod.product_uom.id)
                if not bom_id:
                    raise osv.except_osv(_('Error'), _("Couldn't find bill of material for product"))
                self.write(cr, uid, [prod.id], {'bom_id': bom_id})
                bom_point = self.pool.get('mrp.bom').browse(cr, uid, [bom_id])[0]

            if not bom_id:
                raise osv.except_osv(_('Error'), _("Couldn't find bill of material for product"))

            factor = prod.product_qty * prod.product_uom.factor / bom_point.product_uom.factor
            res = self.pool.get('mrp.bom')._bom_explode(cr, uid, bom_point, factor / bom_point.product_qty, [])
            for r in res[0]:
                if r['product_id']== move.product_id.id:
                    move_lines_obj.write(cr, uid,move.id, {'product_qty' :  r['product_qty']})

        product_lines_obj = self.pool.get('mrp.production.product.line')

        for m in prod.move_created_ids:
            move_lines_obj.write(cr, uid,m.id, {'product_qty' : quantity})

        return {}

    def _update_picking( self,cr,uid,id,try_assign=False, context=None ):
        if context == None:
            context={}

        prod = self.browse(cr,uid,id,context=context)

        cancel_moves =  [x.id for x in prod.picking_id.move_lines]
        lines = []
        for move_line in  prod.move_lines:
            new_mome_id = self.pool.get('stock.move').copy(cr,uid, move_line.id, {'location_dest_id':prod.location_src_id.id, 'picking_id':prod.picking_id.id,'state':'confirmed'}, context = context)
            lines.append(new_mome_id)
        self.pool.get('stock.picking').browse(cr,uid,prod.picking_id.id,context=context)

        self.pool.get('stock.picking').write( cr, uid, prod.picking_id.id, {'move_lines':[(6,0,lines)]}, context=context)
        self.pool.get('stock.move').action_cancel(cr,uid, cancel_moves,context)
        if try_assign:
            self.pool.get('stock.picking')._try_assign(cr, uid, production.picking_id, context)


    def _split(self, cr, uid, id, quantity, context):
        """
        Sets the quantity to produce for production with id 'id' to 'quantity' and
        creates a new production order with the deference between current amount and
        the new quantity.
        """

        production = self.browse(cr, uid, id, context)
        if production.state != 'confirmed':
            raise osv.except_osv(_('Error !'), _('Production order "%s" is not in "Waiting Goods" state.') % production.name)
        if quantity >= production.product_qty:
            raise osv.except_osv(_('Error !'), _('Quantity must be greater than production quantity in order "%s" (%s / %s)') % (production.name, quantity, production.product_qty))

        # Create new production, but ensure product_lines is kept empty.
        new_production_id = self.copy(cr, uid, id, {
            'product_lines': [],
            'move_prod_id': False,
            'product_qty': production.product_qty - quantity,
        }, context)

        self.write(cr, uid, production.id, {
            'product_qty': quantity,
            'product_lines': [],
        }, context)

        self.action_compute(cr, uid, [ new_production_id])
        self._change_prod_qty( cr, uid, production.id ,quantity, context)
        workflow = netsvc.LocalService("workflow")
        workflow.trg_validate(uid, 'mrp.production', new_production_id, 'button_confirm', cr)

        return [id, new_production_id]

mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


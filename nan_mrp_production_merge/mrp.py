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

    _columns = {
        'merged_into_id': fields.many2one('mrp.production', 'Merged into', required=False, readonly=True, help='Production order in which this production order has been merged into.'),
        'merged_from_ids': fields.one2many('mrp.production', 'merged_into_id', 'Merged from', help='List of production orders that have been merged into the current one.'),
    }

    def _merge(self, cr, uid, ids, context):
        """
        Cancels two or more production orders and merges them into a new one. Productions
        must be in 'confirmed' state in order to be merged.
        """

        if len(ids) <= 1:
            return False

        main = self.browse(cr, uid, ids[0], context)
        if main.state != 'confirmed':
            raise osv.except_osv(_('Error !'), _('Production order "%s" is not in "Waiting Goods" state.') % main.name)

        # Create new production, but ensure product_lines is kept empty.
        new_production_id = self.copy(cr, uid, ids[0], {
            'product_lines': [],
            'move_prod_id': False,
        }, context=context)
        new_production = self.browse(cr, uid, new_production_id, context)
        new_move_lines = {}
        new_move_created_ids = {}

        # Consider fields that are NOT required.
        new_bom_id = new_production.bom_id and new_production.bom_id.id or False
        new_routing_id = new_production.routing_id and new_production.routing_id.id or False
        new_product_uos = new_production.product_uos and new_production.product_uos.id or False

        product_qty = 0
        product_uos_qty = 0
        picking_ids = []
        for production in self.browse(cr, uid, ids, context):
            if production.state != 'confirmed':
                raise osv.except_osv(_('Error !'), _('Production order "%s" is not in "Waiting Goods" state.') % production.name)
            # Check required fields are equal
            if production.product_id != new_production.product_id:
                raise osv.except_osv(_('Error !'), _('Production order "%s" product is different from the one in the first selected order.') % production.name)
            if production.product_uom != new_production.product_uom:
                raise osv.except_osv(_('Error !'), _('Production order "%s" UOM is different from the one in the first selected order.') % production.name)

            # Check not required fields are equal
            bom_id = production.bom_id and production.bom_id.id or False
            if bom_id != new_bom_id:
                raise osv.except_osv(_('Error !'), _('Production order "%s" BOM is different from the one in the first selected order.') % production.name)

            routing_id = production.routing_id and production.routing_id.id or False
            if routing_id != new_routing_id:
                raise osv.except_osv(_('Error !'), _('Production order "%s" routing is different from the one in the first selected order.%s - %s') % (production.name, production.routing_id, new_production.routing_id) )

            product_uos = production.product_uos and production.product_uos.id or False
            if product_uos != new_product_uos:
                raise osv.except_osv(_('Error !'), _('Production order "%s" UOS is different from the one in the first selected order.') % production.name)

            product_qty += production.product_qty
            product_uos_qty += production.product_uos_qty

            picking_ids.append( production.picking_id.id )


        self.write(cr, uid, [new_production_id], {
            'product_qty': product_qty,
            'product_uos_qty': product_uos_qty,
        }, context )

        # As workflow calls may commit to db we do it at the very end of the process
        # so we minimize the probabilities of problems.

        self.action_compute(cr, uid, [new_production_id])
        workflow = netsvc.LocalService("workflow")
        workflow.trg_validate(uid, 'mrp.production', new_production_id, 'button_confirm', cr)

        self.write(cr, uid, ids, {
            'merged_into_id': new_production_id,
        }, context)

        # Cancel 'old' production: We must cancel pickings before cancelling production orders
        for id in picking_ids:
            workflow.trg_validate(uid, 'stock.picking', id, 'button_cancel', cr)
        for id in ids:
            workflow.trg_validate(uid, 'mrp.production', id, 'button_cancel', cr)

        return new_production_id

mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

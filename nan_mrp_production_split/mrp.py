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

    #_columns = {
        #'split_into_id': fields.many2one('mrp.production', 'Merged into', required=False, readonly=True, help='Production order in which this production order has been merged into.'),
        #'merged_from_ids': fields.one2many('mrp.production', 'merged_into_id', 'Merged from', help='List of production orders that have been merged into the current one.'),
    #}

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
        }, context)

        self.action_compute(cr, uid, [id, new_production_id])
        workflow = netsvc.LocalService("workflow")
        workflow.trg_validate(uid, 'mrp.production', new_production_id, 'button_confirm', cr)

        return [id, new_production_id]

mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

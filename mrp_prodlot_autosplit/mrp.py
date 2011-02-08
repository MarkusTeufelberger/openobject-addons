# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
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

from osv import fields
from osv import osv
from tools.translate import _


class mrp_production(osv.osv):
    _inherit = "mrp.production"

    def action_confirm(self, cr, uid, ids):
        result = super(mrp_production, self).action_confirm(cr, uid, ids)

        if self.pool.get('ir.model.fields').search(cr, uid, [('name', '=', 'company_id'), ('model', '=', 'mrp.production')]):
            version = '6'
        else:
            version = '5'

        new_ids = []
        for production in self.browse(cr, uid, ids):
            if version == '6':
                # OpenERP v6 have the field company_id on the stock_picking but v5 doesn't have it, 
                # so we use user_id to found the company
                autosplit = production.company_id.autosplit_is_active
            else:
                user = self.pool.get('res.users').browse(cr, uid, uid)
                autosplit = user.company_id.autosplit_is_active

            if not autosplit:
                continue

            for move in production.move_created_ids:
                if not move.product_id.unique_production_number:
                    continue 
                if move.product_qty > 1 and move.product_id.track_production:
                    new_ids += self.pool.get('stock.move').split_move_in_single(cr, uid, [move.id])

        for move in self.pool.get('stock.move').browse(cr, uid, new_ids):
            lot_id = self.pool.get('stock.production.lot').create(cr, uid, {
                'product_id': move.product_id.id,
            })
            self.pool.get('stock.move').write(cr, uid, [move.id], {
                'prodlot_id': lot_id,
            })
        return result

mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

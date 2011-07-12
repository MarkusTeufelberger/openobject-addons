# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Santiago Argüeso Armesto$
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

"""creates serial numbers in production"""

from osv import osv

class mrp_production(osv.osv):

    _inherit = "mrp.production"

   
    def action_in_production(self, cr, uid, ids):
        """orders to create serials"""
        for production in self.browse(cr, uid, ids):
            for finish_move in production.move_created_ids:
                if finish_move.product_id.sn_required == True:
                    finish_move.create_serials()

        return super(mrp_production, self).action_in_production(cr, uid, ids)


    def action_production_end(self, cr, uid, ids):
        """assigns serial to picking"""
        obj = self.browse(cr, uid, ids)
        for prod in obj:
            # if exist a movement from the procurement
            if prod.move_prod_id:
                for move_created in  prod.move_created_ids:
                    if move_created.product_id.id == prod.move_prod_id.product_id.id:
                        vals =  {
                         'sn_ids':[(6, 0, map(lambda x:x.id, move_created.sn_ids or []))]
                        }
                        prod.move_prod_id.write(vals)

        return super(mrp_production,self).action_production_end(cr, uid, ids)

mrp_production()

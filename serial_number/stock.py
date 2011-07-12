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

"""adds new serial number fields to stock.moves"""

from osv import osv, fields
import pooler

class stock_move(osv.osv):

    _inherit = "stock.move"

    _columns = {
        'sn_ids':fields.many2many('serial.number', 'serial_move_rel','move_id', 'sn_id', 'Serial numbers')
    }

    def create_serials(self, cr, uid,ids, context=None):
        """Create serial numbers for movement"""
        for move in self.browse(cr,uid,ids):
            if move.product_id.sn_required == True:
                for i in range (0,move.product_qty):
                    vals =  {
                         'move_ids':[(6, 0, [move.id])]
                    }
                    context={
                        'product_id':move.product_id.id,

                    }
                    self.pool.get('serial.number').create(cr,uid,vals ,context)

stock_move()

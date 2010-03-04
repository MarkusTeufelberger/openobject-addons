# -*- encoding: utf-8 -*-
#########################################################################
#This module intergrates Open ERP with the magento core                 #
#Core settings are stored here                                          #
#########################################################################
#                                                                       #
# Copyright (C) 2009  Raphaël Valyi                                     #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields,osv

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        if view_type == 'form' and context.get('view', False) == 'rma':
            view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name','=','stock.picking.rma.form')])[0]
        return  super(stock_picking, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)

stock_picking()


class stock_move(osv.osv):
    _inherit = "stock.move"

    def _default_product_id(self, cr, uid, context={}):
        return context.get('product_id', False)
    
    def _default_prodlot_id(self, cr, uid, context={}):
        return context.get('prodlot_id', False)
    
    def _default_location_id(self, cr, uid, context={}):
        return context.get('location_id', False) or super(stock_move, self)._default_location_source(cr, uid, context)
    
    def _default_location_dest_id(self, cr, uid, context={}):
        return context.get('location_dest_id', False) or super(stock_move, self)._default_location_destination(cr, uid, context)
    
    def _default_name(self, cr, uid, context={}):
        return "RMA_move"
    
    _defaults = {
        'product_id': _default_product_id,
        'prodlot_id': _default_prodlot_id,
        'location_id': _default_location_id,
        'location_dest_id': _default_location_dest_id,
        'name': _default_name,
    }

stock_move()
# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    sale_bundle_product for OpenERP                                          #
# Copyright (c) 2011 CamptoCamp. All rights reserved. @author Joel Grand-Guillaume #
#                                                                               #
#    This program is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU Affero General Public License as             #
#    published by the Free Software Foundation, either version 3 of the         #
#    License, or (at your option) any later version.                            #
#                                                                               #
#    This program is distributed in the hope that it will be useful,            #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#    GNU Affero General Public License for more details.                        #
#                                                                               #
#    You should have received a copy of the GNU Affero General Public License   #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                               #
#################################################################################

from osv import osv, fields
import netsvc


class sale_order_line(osv.osv):
    
    _inherit = "sale.order.line"
    

    _columns = {
        'so_line_item_set_ids':fields.many2many('sale.order.line.item.set', 'so_line_so_item_set_rel','sale_order_line_id', 'so_item_set_id','Choosen configurtion'),
    }


sale_order_line()


# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

{
    "name" : "Purchase and Sale Delivery Cost",
    "description" : """Delivery cost and delivery management for purchases and sales""",
    "version" : "1.0",
    "author" : "Pexego",
    "depends" : ["base","product","account","delivery","purchase","stock","sale","purchase_discount"],
    "category" : "My Modules/Calor Color",
    "init_xml" : [],
    "update_xml" : ['security/ir.model.access.csv',
                    'purchase_order_view.xml',
                    'delivery_wizard.xml',
                    'stock_picking_view.xml',
                    'freight_tobe_collected_view.xml',
                    'product_view.xml',
                    'sale_view.xml',
                    'sale_wizard.xml',
                    'stock_move_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai (gdukai@gmail.com)
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
    "name": "Price list discount and tax handling",
    "version": "1.11",
    "author": "Gábor Dukai",
    "website" : "http://exploringopenerp.blogspot.com",
    "category": "Generic Modules/Inventory Control",
    "description": """
    A complete solution for those companies who use discounts and/or 
    product prices with tax included extensively.
    
    This module is like product_visible_discount but improved in many ways:
      -Properly calculates discounts for any price type, not only list_price.
      -It's able to add/subtract tax from the price before calculating the discount.
      This means you can have for example a 'shop price' calculated with tax included
      and define a price list like 'shop price net -5%' easily.
      -It works with product_price_update that module can mass calculate and 
      update product prices with tax included.
      -A simpler override of the SO's product_id_change, 2 browses and 2 reads less.
      -Purchase Orders can also use discounts if the supplier defines his prices
      with discounts.
      -Even PO's generated with MRP will have the discounts defined in the 
      supplier price list.
    
    Compatibility: tested with OpenERP v5.0
    """,
    "depends": ["sale", "purchase_discount", ],
    "demo_xml": [],
    "update_xml": [
        'pricelist_view.xml',
    ],
    "license": "GPL-3",
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


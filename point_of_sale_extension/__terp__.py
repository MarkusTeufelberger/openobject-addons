# -*- coding: utf-8 -*-
##############################################################################
#
#    point_of_sale_extension module for OpenERP, profile for 2ed customer
#
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) 
#       All Rights Reserved, Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 SYLEAM (http://syleam.fr) 
#       All Rights Reserved, Christophe Chauvet <christophe.chauvet@syleam.fr>
#
#    This file is a part of point_of_sale_extension
#
#    point_of_sale_extension is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    point_of_sale_extension is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Point Of Sale Extension",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Generic Modules/Sales & Purchases",
    "website": "http://www.zikzakmedia.com",
    "description": """
* Only it allows delete draft or canceled POS orders and POS order lines.
* If POS order has a partner, the partner is stored in:
    - The stock.picking created by the pos order.
    - The account.move.line created by the pos order.
* POS orders with amount_total==0 no creates account moves (it gives error).
* Shows the payment type (journal) in the payments list in teh second tab of the POS.
* The journals used to pay with the POS can be choosed (in the configuration tab of the company: Administration / Users / Companies).
* Product prices with or without taxes included (select in the configuration tab of the company).
* Shows a warning in the payment wizard (but you can continue) if:
    - A product added in the POS order has already been requested by the partner (the partner has a sale order with this product), so the user can decide if is better to do a POS order from a sale order.
    - There is not enough virtual stock in any of the products.
  These two warnings can be activated/desactivated (in the configuration tab of the company).
* List and search POS order lines by number of order, partner and state.
* If product_visible_discount module is installed and visible discount field in price list is checked, computes discounts in point of sale order lines.
""",
    "depends" : ["point_of_sale"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "security/ir.model.access.csv",
        "company_view.xml",
        "pos_wizard.xml",
        "pos_view.xml",
    ],
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

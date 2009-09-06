# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                    Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright (c) 2009 SYLEAM (http://syleam.fr) Al Rights Reserved
#                    Christophe Chauvet <christophe.chauvet@syleam.fr>
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

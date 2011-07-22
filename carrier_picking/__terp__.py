# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
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
    "name" : "Carrier picking adds carrier contact information",
    "version" : "0.1",
    "author" : "Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "license" : "GPL-3",
    "category" : "Generic Modules/Others",
    "description": """Carrier picking module:
* Allows to check the partners as shipping agencies or carriers.
* Adds the shipping agency partner in picking lists.
* Adds the carrier partner and carrier address in picking lists.
* Adds a field to store the vehicle's plate (or other info) in partner addresses and picking lists.
* Allows to check the products as a shipping products. You can store zip, city, state and country information for the from and to destination of the shipping product.""",
    "depends" : ["base","stock"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "stock_view.xml",
        "partner_view.xml",
        "product_view.xml",
    ],
    "active": False,
    "installable": True
}

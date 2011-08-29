# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Product Trademark (manufacturer)",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website": "www.zikzakmedia.com",
    "license" : "Affero GPL-3",
    "category" : "Generic Modules/Others",
    "description": """
        This module add same fields to Product Manafucturer developed by OpenERP S.A except Attributes (only Manufacturer Information).
        At Sale, Purchase and Stock lines, manufacturer field is available.
    """,
    "depends" : [
        "purchase",
        "product",
        "sale",
        "stock",
    ],
    "init_xml" : [],
    "update_xml" : [
        "purchase_view.xml",
        "product_view.xml",
        "sale_view.xml",
        "stock_view.xml",
    ],
    "active": False,
    "installable": True
}

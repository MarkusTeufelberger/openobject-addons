# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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
    "name" : "Product CSV",
    "version" : "0.1",
    "author" : "Zikzakmedia SL",
    "website" : "http://www.zikzakmedia.com",
    "category" : "Generic Modules/Inventory Control",
    "description": """
Import CSV file in product object:
- Design mapping CSV to OpenERP fields (modify default product_csv_product and product_csv_product_template mapping at Administration/Customization/Database Structure/CSV File)
- Mark in product_csv_product SKU field mapping
    """,
    "license" : "GPL-3",
    "depends" : [
        "base_csv",
        "product",
    ],
    "init_xml" : [
        "settings/base_csv_mapping.xml",
    ],
    "update_xml" : [
        "product_csv_view.xml",
        "wizard/import_csv_view.xml"
        ],
    "active": False,
    "installable": True
}

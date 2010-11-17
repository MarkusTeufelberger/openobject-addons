# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2010 Zikzakmedia. All Rights Reserved
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
    "name" : "Product BoM duplication",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Generic Modules/Inventory Control",
    "website": "http://www.zikzakmedia.com",
    "description": """If you install this module, when a product is duplicated,
all Bill of Materials of this product are also duplicated.
""",
    "depends" : [
        "mrp"
    ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

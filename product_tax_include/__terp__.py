# -*- coding: utf-8 -*-
##############################################################################
#
#    product_tax_include module for OpenERP, Add new field for tax include in product
#    Copyright (C) 2009 SYLEAM Info Services (<http://www.Syleam.fr/>) Sebastien LANGE
#
#    This file is a part of product_tax_include
#
#    product_tax_include is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    product_tax_include is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Product Tax Include',
    'version': '0.0.1',
    'category': 'Generic Modules/Inventory Control',
    'description': """Add new field for tax include in product

 OpenERP version : 5.0
 Creation : 2009-12-05
 Last update : 2009-12-05
""",
    'author': 'SYLEAM Info Services',
    'depends': [
                "base",
                "product",
                "account_tax_include",
    ],
    'init_xml': [],
    'update_xml': [
        "view/company.xml",
        "view/product.xml",
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- coding: utf-8 -*-
##############################################################################
#
#    product_tax_category module for OpenERP
#    Copyright (C) 2009 SYLEAM (<http://www.syleam.fr>) Christophe CHAUVET
#
#    This file is a part of product_tax_category
#
#    product_tax_category is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    product_tax_category is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Product Category Extended',
    'version': '0.1.a',
    'category': 'Custom',
    'description': """
    Add On Change on product category to:
    * Fill sales and purchase taxes on product.
    * Add default UOM on product
    """,
    'author': 'Syleam',
    'depends': [
        'product',
        'stock',
        'account',
    ],
    'init_xml': [],
    'update_xml': [
        'view/product.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

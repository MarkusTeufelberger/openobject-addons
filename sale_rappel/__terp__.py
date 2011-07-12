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
        "name" : "Sales Rappel",
        "version" : "0.1",
        "author" : "Pexego",
        "website" : "http://www.pexego.es",
        "category" : "Enterprise Specific Modules",
        "description": """
            * Allow to include a percentage of rappel in sales and it will be reflected in invoices and pickings
            * You must configure rappel product accounts ior rappel product category accounts
            """,
        "depends" : ['base', 'sale', 'account', 'stock', 'product'],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                'data/product_product.xml',
                'sale_view.xml',
                'account_invoice_view.xml'
                ],
        "installable": True
}

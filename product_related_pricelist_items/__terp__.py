# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 Gábor Dukai <gdukai@gmail.com>
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
    "name": "Product related price list items",
    "version": "1.0",
    "author":"Gábor Dukai",
    "website" : "http://exploringopenerp.blogspot.com",
    "category": "Generic Modules/Inventory Control",
    "description": """
    A convenience wizard on the product form to show and edit only the
    price list items that are relevant. This means that you can choose a
    price list version from the product form and you get an editable grid
    with only those items that are defined for that product or
    it's categories (including some parents) or aren't restricted at all.

    NOTE: Needs the --enable-code-actions parameter for the server.
    Compatibility: tested with OpenERP v5.0
    """,
    "depends":["product"],
    "demo_xml":[],
    "update_xml":[
        'security/ir.model.access.csv',
        'pricelist_action.xml',
        'pricelist_view.xml',
    ],
    "license": "GPL-3",
    "active":False,
    "installable":True,
}

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Zikzakmedia SL (http://www.zikzakmedia.com)
#    Copyright (c) 2011 NaN Projectes de Programari Lliure S.L. (http://nan-tic.com)
#    Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
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
    "name" : "Stock valued",
    "version" : "0.3",
    "author" : "Pablo Rocandio, ACYSOS, S.L., NaN·tic, Zikzakmedia SL",
    "category": "Generic Modules/Inventory Control",
    "description": """Add amount information to pickings.""",
    "license" : "GPL-3",
    "depends" : ["base", "account", "stock", "sale"],
    "init_xml" : [],
    "update_xml" : [
        #'security/ir.model.access.csv',
        'stock_valued_view.xml',
        'stock_valued_report.xml',
                   ],
    "active": False,
    "installable": True
}


# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
	"name" : "Company currency in invoices",
	"version" : "1.0",
	"author" : "Zikzakmedia",
	"website" : "http://www.zikzakmedia.com",
    "license" : "GPL-3",
	"depends" : ["account"],
	"category" : "Localisation/Accounting",
	"description": """
Adds functional fields to show Amount Untaxed, Amount Tax and Amount Total invoice fields in the company currency. These fields are shown in "Other information" tab in invoice form. 
""",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [
		"account_invoice_view.xml",
	],
	"active": False,
	"installable": True
}

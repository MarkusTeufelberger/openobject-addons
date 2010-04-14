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
	"name" : "Update account chart from template",
	"version" : "1.0",
	"author" : "Zikzakmedia SL",
	"website" : "www.zikzakmedia.com",
    "license" : "GPL-3",
	"depends" : ["account"],
	"category" : "Generic Modules/Accounting",
	"description": """
Adds a wizard to update a company account chart from a template:
  * Generates the new accounts from the template and assigns them to the right company
  * Generates the new taxes and tax codes, changing account assignations
  * Generates the new fiscal positions, changing account and taxes assignations

Before creating the new accounts, taxes, tax codes and fiscal positions, the user can select
which ones must be created.

The user can also choose to update the existing accounts, taxes, tax codes and fiscal positions
from a template.

The problems occurred during the creation/updating of the account chart are shown in the last step.

It is useful when the account law has changed and you want to transfer the new accounts, taxes and
fiscal positions included in the account chart template to an existing company account chart.

Note: Due to the memory limitation of the osv_memory OpenERP objects, only a maximum number of 
objects can be created each time. If a lot of new accounts, taxes, tax codes or fiscal positions
must be created, the wizard should be run several times.
""",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [
		"account_view.xml",
        "security/ir.model.access.csv",
	],
	"active": False,
	"installable": True
}

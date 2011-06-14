# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
    "name" : "Multi Company Share",
    "author" : "Zikzakmedia SL",
    "website" : "http://www.zikzakmedia.com",
    "description" : """
By default the Partners, Partner Address and Products are created associated to the company that the user belongs at that moment.
This module allow you to configure (in the company form) if Partner, Partner Address or Products must be shared between companies or must be linked to the company users.
    """,
    "version" : "0.1",
    "depends" : [
        "base",
        "product",
    ],
    "init_xml" : [],
    "update_xml" : [
        "multi_company_view.xml",
    ],
    "category" : "Multi Company",
    "active": False,
    "installable": True
}

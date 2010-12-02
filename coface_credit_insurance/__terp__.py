# -*- coding: utf-8 -*-
#########################################################################
#
#    Copyright (C) 2010 Anevia
#    Author : Sébastien Beau <sebastien.beau@akretion.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

{
    "name" : "Import of Coface credit assurance information",
    "version" : "1.0",
    "license": "AGPL-3",
    "depends" : ["base"],
    "author" : "Anevia",
    "description": """This module imports the credit insurance information from Coface's webservice and write them to the partner form in OpenERP.
    It uses Kettle (ETL of the Pentaho project) with OOOR (OpenObject On Rails) to connect to the webservice and parse the CSV file of Coface.
""",
    "website" : "http://www.anevia.com/",
    "category" : "Generic Modules/Others",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["partner_view.xml"],
    "active": False,
    "installable": True,

}

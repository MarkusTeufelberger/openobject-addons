# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai <gdukai@gmail.com>
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
    "name" : "Label printing SLCS language support",
    "version" : "1.0",
    "author" : "Gábor Dukai",
    "website" : "http://exploringopenerp.blogspot.com",
    "license" : "GPL-3",
    "category" : "Generic Modules",
    "description": """
    Adds support for SLCS command label templates that are used
    with Bixolon (Samsung) label printers.

    The whole SLCS-related logic is in a mako template file which
    makes it flexible to work with.

    To send the generated command file to the printer, use the
    printjob module.

    Compatibility: tested with OpenERP v5.0
    """,
    "depends" : ["label",],
    "init_xml" : [
    ],
    "demo_xml" : [],
    "update_xml" : [
        "report_label_data.xml",
    ],
    "active": False,
    "installable": True
}

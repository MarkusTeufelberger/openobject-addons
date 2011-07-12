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
    "name" : "Report Notes",
    "description" : """Generic object where you could add translatable notes to include in reports""",
    "version" : "1.0",
    "author" : "Pexego",
    "depends" : ["base"],
    "category" : "Reports",
    "init_xml" : [],
    "update_xml" : ['report_notes_view.xml',
                    'security/ir.model.access.csv'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

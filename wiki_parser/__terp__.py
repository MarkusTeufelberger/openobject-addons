# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Santiago Argüeso Armesto$
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
    'name': 'Wiki parser',
    'version': '1.0',
    'category': 'Generic Modules',
    'description': """
    Adds a parser for wiki pages. It creates pages and evaluates them when create or write according to some regulrar expressions that extract data from OpenERP.
	Serves as a base for other modules that introduces fields in the wiki model to run the parser.
    Pending of error handling, so that if the page syntax is incorrect it displays an error from OpenERP.
    """,
    'author': 'Pexego Sistemas Informaticos',
    'website': 'http://www.pexego.es',
    'depends': ['wiki'],
    'init_xml': [],
    'update_xml': [
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}


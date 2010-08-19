# -*- coding: utf-8 -*-
##############################################################################
#
#    wiki_extension module for OpenERP, Add new field for tax include in product
#    Copyright (C) 2009 SYLEAM Info Services (<http://www.Syleam.fr/>) Sebastien LANGE
#
#    This file is a part of wiki_extension
#
#    wiki_extension is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wiki_extension is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Document Management - Wiki Extension',
    'version': '1.0',
    'category': 'Generic Modules/Others',
    'description': """
    The base module to manage documents(wiki) 

    Add new features :
    - members in wiki groups
    - state in page wiki (Running, Raed Only, Obsolete)
    - improvement view
    """,
    'author': 'SYLEAM Info Services',
    'website': 'http://Syleam.fr',
    'depends': [
        'base',
        'wiki'
        ],
    'init_xml': [],
    'update_xml': [
        'view/wiki_view.xml',
    ],
    'demo_xml': [
        ],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

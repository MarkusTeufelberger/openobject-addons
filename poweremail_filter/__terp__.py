# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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
    'name': 'Poweremail Filter',
    'version': '0.1',
    'category': 'Added functionality',
    'description': """Design your filters some model and send automatically emails (sheduler)""",
    'author': 'Zikzakmedia SL',
    'website': 'http://www.zikzakmedia.com',
    'depends': [
        'base',
        'poweremail'
        ],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'poweremail_filter_view.xml',
        'poweremail_filter_data.xml',
        ],
    'demo_xml': [],
    'installable': True,
 } 

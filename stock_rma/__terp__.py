# -*- encoding: utf-8 -*-
#########################################################################
#This module intergrates Open ERP with the magento core                 #
#Core settings are stored here                                          #
#########################################################################
#                                                                       #
# Copyright (C) 2009  Raphaël Valyi                                     #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    "name" : "stock rma",
    "version" : "0.1",
    "author" : "Akretion.com",
    "description": """Return Material Authorization
    """,
    'website': 'http://www.akretion.com',
    'depends': ["stock", "crm", "crm_configuration", "sale"],
    'init_xml': [],
    'update_xml': ['stock_data.xml', 'crm_view.xml', 'crm_sequence.xml', 'stock_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

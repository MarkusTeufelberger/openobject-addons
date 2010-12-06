# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Created by Luc De Meyer
#    Copyright (c) 2010 Noviat nv/sa (www.noviat.be). All rights reserved.
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
    'name': 'Account CODA - Import bank CODA V2 statements',
    'version': '1.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Localisation/Belgium',
    'description': '''
    Module to import CODA bank statements.

    Supported are CODA flat files in V2 format from bank accounts with Belgian IBAN structure.
    
    This module is derived from account_coda, modifications are extensive:
    - CODA v2.2 support.
    - Support for all data record types (0, 1, 2, 3, 4, 8, 9).
    - Parsing & logging of all Transaction Codes and Structured Format Communications.
    - Automatic Financial Journal assignment via additional IBAN configuration field on the Financial Journals.
    - Support for multiple statements from different bank accounts in a single CODA file.
    - Multi-language CODA parsing, parsing configuration data provided for EN, NL, FR.
    ''',
    'depends': ['account','base_iban'],
    'demo_xml': [],
    'init_xml': [
        'account_coda_trans_type.xml',
        'account_coda_trans_code.xml',     
        'account_coda_trans_category.xml',                
        'account_coda_comm_type.xml',
    ],
    'update_xml' : [
        'security/ir.model.access.csv',
        'account_coda_wizard.xml',
        'account_coda_view.xml'
    ],
    'active': False,
    'installable': True,
}


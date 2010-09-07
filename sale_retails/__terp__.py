# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_retails module for OpenERP, allows the management of deposit
#    Copyright (C) 2010 SYLEAM Info Services (<http://www.syleam.fr/>) Suzanne Jean-Sebastien
#
#    This file is a part of sale_retails
#
#    sale_retails is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_retails is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Sale Retails',
    'version': '0.0.1',
    'category': 'Custom',
    'description': """allows the management of deposit""",
    'author': 'SYLEAM Info Services',
    'depends': [
        'sale',
        'account',
        ],
    'init_xml': [],
    'update_xml': [
        'view/account_view.xml',
        'view/invoice_view.xml',
        'view/sale_view.xml',
        'workflow/sale_workflow.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

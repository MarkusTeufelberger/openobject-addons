# -*- coding: utf-8 -*-
##############################################################################
#
#    hr_expenses_supplier module for OpenERP, add supplier in expenses lines
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
#
#    This file is a part of hr_expenses_supplier
#
#    hr_expenses_supplier is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    hr_expenses_supplier is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'HR Expenses Supplier',
    'version': '1.0',
    'category': 'Generic Modules/HR',
    'description': """
    Add supplier on expenses lines for generate invoice supplier
    if the employe didn't paid the expenses but the company
    """,
    'author': 'SYLEAM Info Services',
    'website': 'http://www.Syleam.fr',
    'depends': ['base',
                'hr_expense',
               ],
    'init_xml': [],
    'update_xml': [
        'view/hr_expenses.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'license': 'GPL-3',
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


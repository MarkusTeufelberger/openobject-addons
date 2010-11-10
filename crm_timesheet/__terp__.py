# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2008-2009 Syleam (<http://syleam.fr>). All Rights Reserved
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
    'name': 'CRM Timesheet',
    'version': '1.0.2',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
    Add timesheet on CRM (the same method as task's project),
    On partner form, CRM Analytic tab, define analytic account by CRM Section
    Define the default analytic account on each section
    Fill your summary work on the crm case.
    """,
    'author': 'Syleam',
    'depends': [
        'base',
        'crm',
        'hr_timesheet'
    ],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'view/crm_timesheet.xml',
        'view/partner.xml',
        'view/crm_section.xml',
        'view/account_analytic.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

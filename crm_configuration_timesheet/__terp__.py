# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2009 SYLEAM (<http://syleam.fr>). All Rights Reserved
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
    'name': 'CRM Configuration Timesheet',
    'version': '5.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
    Add timesheet on CRM configuration (the same method as task's project),
    On partner form, CRM Analytic tab, define analytic account by CRM Section
    Define the default analytic account on each section
    Fill your summary work on the crm configuration.
""",
    'author': 'Syleam',
    'website': 'http://www.Syleam.fr',
    'depends': ['base', 'crm', 'crm_configuration', 'hr_timesheet', 'crm_timesheet'],
    'init_xml': [
    ],
    'update_xml': [
        'view/crm_bugs_timesheet_view.xml',
        'view/crm_claims_timesheet_view.xml',
        'view/crm_fund_timesheet_view.xml',
        'view/crm_jobs_timesheet_view.xml',
        'view/crm_lead_timesheet_view.xml',
        'view/crm_meetings_timesheet_view.xml',
        'view/crm_opportunity_timesheet_view.xml',
        'view/crm_phonecall_timesheet_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

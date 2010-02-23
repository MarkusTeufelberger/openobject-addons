# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
    "name" : "Project Portal",
    "version" : "1.0",
    "author" : "Tiny",
    "category" : "Generic Modules/CRM",
    "description": """ This module allows customers to connect on Project Portal and
manage their projects very easily. Customers can be able to manage everything
related to a project:
  - Tasks
  - Timesheets
  - Bugs (bugtracker)
  - Feature Requests
  - Wiki Page
  - Financial Data
  - Invoices
  - Documents
  - Dashboard
""",
    "depends" : ["crm", "portal", "project_event", "hr_timesheet_sheet", "wiki", "project_planning", "account_analytic_analysis", "project_crm", "document", "board_project"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["portal_project_wizard.xml", "portal_project_view.xml", "portal_project_data.xml"],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

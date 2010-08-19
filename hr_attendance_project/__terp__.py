# -*- coding: utf-8 -*-
##############################################################################
#
#    hr_attendance_project module for OpenERP
#    Copyright (C) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#       Raimon Esteve <resteve@zikzakmedia.com> All Rights Reserved.
#       Jordi Esteve <resteve@zikzakmedia.com> All Rights Reserved.
#
#    This file is a part of hr_attendance_project
#
#    hr_attendance_project is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    hr_attendance_project is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Attendances of Employees in Projects",
    "version" : "1.0",
    "author" : "Zikzakmedia",
	"website" : "www.zikzakmedia.com",
    "license" : "GPL-3",
    "description" : """This module aims to manage employee's attendances in Projects.

Adds a new wizard to sign in/sign out. In the sign out, an analitic account or a project must be given, and a task of this analitic account or project. A work for this task with user, start date and hour information is created.""",
    "depends" : ["base","account","hr_attendance","project","project_timesheet","hr_timesheet"],
    "init_xml" : [],
    "update_xml" : [
		"hr_attendance_project_wizard.xml",
    ],
    "category" : "Generic Modules/Human Resources",
    "active": False,
    "installable": True
}

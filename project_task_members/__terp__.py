# -*- coding: utf-8 -*-
##############################################################################
#
#    project_task_members module for OpenERP, Add task's members in project
#    Copyright (C) 2009 SYLEAM Info Services (<http://www.Syleam.fr/>) Sebastien LANGE
#
#    This file is a part of project_task_members
#
#    project_task_members is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    project_task_members is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Project Task Members',
    'version': '1.0.1',
    'category': 'Generic Modules/Projects & Services',
    'description': """Add task's members in project

 OpenERP version : 5.0
 Creation : 2009-12-19
 Last update : 2009-12-26
""",
    'author': 'SYLEAM Info Services',
    'depends': [
                'base',
                'project',
    ],
    'init_xml': [
    ],
    'update_xml': [
        'view/project_task.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

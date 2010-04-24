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

from osv import fields, osv
from tools.translate import _

class task(osv.osv):
    _inherit = 'project.task'
    _columns = {
         'member_ids': fields.many2many('res.users', 'project_task_user_rel', 'task_id', 'uid', 'Task Members', help="Task's member. Not used in any computation, just for information purpose."),
    }

task()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

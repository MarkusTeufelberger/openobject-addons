# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Borja López Soilán$
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

from osv import fields, osv

class scrum_task(osv.osv):
    _inherit = 'scrum.task'

    _columns = {
        'code': fields.char('Req Id', size=12, select=1),
        'project_id': fields.many2one('scrum.project', 'Project', ondelete='cascade',
            help="If you have [?] in the project name, it means there are no analytic account linked to this project."),
    }

    _defaults = {
        'planned_hours': lambda *a: 0,
    }

scrum_task()

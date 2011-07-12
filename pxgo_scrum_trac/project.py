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

class project_project(osv.osv):
    _inherit = 'scrum.project'

    _columns = {
        'tickets_trac_url': fields.char('Url Tickets', size=64, help="Url to concatenate to ticket number for each requirement for access to Trac to ticket."),
        'trac_project': fields.char('Project name on Trac', size=64, help='Project name on Trac'),
        'xmlrpc_url': fields.char('XMLRPC URL', size=64, help='URL for remote access by XMLRPC to Trac, example: http://scrum.pxgo.es/proyecto/xmlrpc'),
        'xmlrpc_timezone_diff_hours': fields.integer('Timezone diff', required=False, select=2, help="Timezone difference (in hours) applied when sync, example: 2"),
        'ticket_type_story': fields.char('Story', size=64, help="Ticket type used as user story, example: product_backlog"),
        'ticket_type_task': fields.char('Task', size=64, help="Ticket type used as Task, eg: task"),
    }

project_project()

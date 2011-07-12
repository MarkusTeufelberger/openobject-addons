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

"""
Information about synchronization with Trac.
"""
__author__ = "Borja López Soilán (Pexego)"


from osv import fields, osv

#-------------------------------------------------------------------------------
# Agente
#-------------------------------------------------------------------------------
class pxgo_scrum_trac_ticket_sync(osv.osv):
    """
    Information about synchronization with Trac.
    """

    _name = "pxgo.scrum.trac.ticket_sync"
    _description = "pxgo_scrum_trac_ticket_sync"

    #
    # Campos -------------------------------------------------------------------
    #

    _columns = {
        'project_id': fields.many2one('scrum.project', 'Project', ondelete='cascade', select=1),
        'ticket': fields.integer('Trac ticket', required=True, select=1),
        'sync_date': fields.datetime('Sync date.', help='Date of last synchronization', select=2),
        'sync_action': fields.selection([('import','Import'), ('import_new','Import new'), ('export','Export'), ('export_new','Export new')], 'Action', select=2)
    }

pxgo_scrum_trac_ticket_sync()

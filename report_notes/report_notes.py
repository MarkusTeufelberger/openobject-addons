# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

"""Generic object where you could add translatable notes to include in reports"""

from osv import osv, fields

class ir_act_report_xml_note(osv.osv):
    """Generic object where you could add translatable notes to include in reports"""

    _name = "ir.act.report.xml.note"

    _columns = {
        'name': fields.char('Name', required=True, help="Descriptive name of note", size=128),
        'active': fields.boolean('Active'),
        'note': fields.text('Note', translate=True)
    }

    _defaults = {
        'active': lambda *a: False
    }

ir_act_report_xml_note()
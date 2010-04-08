# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenOffice Reports
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
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

"""
Extends report_xml to add new report types to the report_type selection.
"""
__author__ = "Borja López Soilán (Pexego)"

from osv import osv, fields

class report_xml(osv.osv):
    """
    Extends report_xml to add new report types to the report_type selection.

    You may declare reports of the new types like this
        <report id="report_REPORTNAME"
			... />
        <record model="ir.actions.report.xml" id="report_REPORTNAME">
	        <field name="report_type">oo-odt</field>
        </record>
    """
    
    _inherit = 'ir.actions.report.xml'

    _columns = {
        'report_type': fields.selection([
                ('pdf', 'pdf'),
                ('html', 'html'),
                ('raw', 'raw'),
                ('sxw', 'sxw'),
                ('odt', 'odt'),
                ('html2html','Html from html'),
                ('oo-pdf', 'OpenOffice - pdf output'),
                ('oo-html', 'OpenOffice - html output'),
                ('oo-odt', 'OpenOffice - odt output'),
                ('oo-doc', 'OpenOffice - doc output'),
                ('oo-rtf', 'OpenOffice - rtf output'),
                ('oo-txt', 'OpenOffice - txt output'),
                ('oo-ods', 'OpenOffice - ods output'),
                ('oo-xls', 'OpenOffice - xls output'),
                ('oo-csv', 'OpenOffice - csv output'),
                ('oo-odp', 'OpenOffice - odp output'),
                ('oo-ppt', 'OpenOffice - ppt output'),
                ('oo-swf', 'OpenOffice - swf output'),
            ], string='Type', required=True),
    }

report_xml()

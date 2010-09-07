# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai <gdukai@gmail.com>
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

from osv import osv

import label_report_engine

class label_templates(osv.osv):
    _inherit = 'label.templates'

    def _report_vals_slcs(self, report_name, src_obj, oerp_full_report_name,
        full_report_name, allowed_groups):
        return {
            'name': report_name,
            'model': src_obj,
            'type': 'ir.actions.report.xml',
            'report_name': oerp_full_report_name,
            'report_xsl': '',
            'report_xml': '',
            'report_rml': '',
            'auto': False,
            'header': False,
            'report_type': 'raw',
            'groups_id': allowed_groups,
        }

    def _instantiate_report_slcs(self, template):
        label_report_engine.report_label_slcs(
            'report.' + template.report_template.report_name,
            template.report_template.model)

label_templates()
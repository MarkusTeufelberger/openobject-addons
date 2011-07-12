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


{
    'name': 'Pexego Scrum Modified, Import and export, tickets, client backlogs and product_backlogs data available from trac',
    'version': '1.0',
    'category': 'My Modules',
    'description': """
        Export trac tickets and product_backlogs in csv and import in openerp.
        * In Trac side you need TractXmlRpc and Bitem.
    """,
    'author': 'Pexego',
    'depends': ['project','scrum'],
    'init_xml': [],
    'update_xml': [
        'pxgo_scrum_trac_view.xml',
        'pxgo_scrum_trac_wizard.xml',
        'ticket_sync_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

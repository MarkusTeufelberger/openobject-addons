# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
# Fixes, improvements and V6 adaptation by Guewen Baconnier - Camptocamp 2011

{
    'name': 'Partner Merger',
    'version': '1.0',
    'category': 'Generic Modules/Base',
    'description': """
To merge 2 partners, select them in the list view and execute the Action "Merge Partners".
To merge 2 addresses, select them in the list view and execute the Action "Merge Partner Addresses" or use the menu item :
 Partners / Configuration / Merge Partner Addresses

The selected addresses/partners are deactivated and a new one is created with :
 - When a value is the same on each resources : the value
 - When a value is different between the resources : you can choose the value to keep in a selection list
 - When a value is set on a resource and is empty on the second one : the value set on the resource
 - All many2many relations of the 2 resources are created on the new resource.
 - All the one2many relations (invoices, sale_orders, ...) are updated in order to link to the new resource.

    """,
    'author': 'OpenERP',
    'website': 'http://www.openerp.com',
    'depends': ['base'],
    'init_xml': [],
    'update_xml': [
                    "wizard/base_partner_merge_view.xml", 
                    "wizard/base_partner_merge_address_view.xml"
                   ],
    'demo_xml': [],
    'installable': True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

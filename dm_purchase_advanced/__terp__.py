# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
{
    "name" : "Advanced Purchase Management for DM",
    "version" : "1.0",
    "author" : "Tiny",
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/Direct Marketing",
    "description": """
            This module adds purchase management for the 4 departments of direct marketing
            (manufacturing, files, items and DTP)
            """,
    "depends" : ["dm_purchase","purchase_tender"],
    "init_xml" : [],
    "demo_xml" : ["dm_purchase_advanced_demo.xml"],
    "update_xml" : [
                    "security/ir.model.access.csv",
                    "dm_purchase_advanced_wizard.xml",
                    "dm_purchase_advanced_view.xml",
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


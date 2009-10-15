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
    "name" : "Account l10nbe Domiciliation",
    "version" : "1.0",
    "author" : "Tiny",
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/Account l10nbe Domiciliation",
    "description": """
        Related with l10n_be module.
        Adds Domiciled and Domiciled send date fields on invoice.
        Domiciliation and Domiciliation Number fields on partner.
    """,
    "depends" : ["base","account"],
    "init_xml" : [],
    "demo_xml" : [],

    "update_xml" : ["l10nbe_domiciliation_view.xml", 
                            "l10nbe_domiciliation_report.xml",
                            "l10nbe_domiciliation_wizard.xml"
                            ],
    "active": False,
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


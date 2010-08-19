# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2009 Smile.fr. All Rights Reserved
#    authors: Raphaël Valyi, Xavier Fernandez
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
    "name" : "MultiStep Product Configurator",
    "description" : "Generic Multistep configurator",
    "version" : "0.5",
    "author" : "Smile",
    "website": "http://www.smile.fr",
    "category" : "Generic Modules/Sales",
    "depends" : ["sale"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [    "security/ir.model.access.csv",
                        "sale_product_multistep_configurator.xml",
                        "sale_product_multistep_configurator_wizard.xml",
                        "sale_view.xml"
                    ],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Price Adjustment Addon for OpenERP
#    Copyright (C) 2004-2009 Bubbles-IT (<http://bubbles-it.be>). All Rights Reserved
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

{
    "name" : "Price Adjust Wizard",
    "version" : "0.1",
    "author" : "Niels Huylebroeck",
    "description" : """Price Adjust Wizard
This wizard will allow you to adjust Cost Price and Sale Price for entire categories.
You can either set a fixed price or use a multiplier to increase or decrease the price.
It also records a history of price changes in the past.""",
    "website" : "http://www.bubbles-it.be",
    "depends" : ["product","sale"],
    "category" : "Generic Modules/Sales & Purchases",
    "demo_xml" : [],
    "update_xml" : [
        "security/ir.model.access.csv",
    	"price_adjust_wizard.xml",
	    "price_adjust_view.xml"
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

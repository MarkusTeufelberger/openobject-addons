# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Joel Grand-guillaume (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    "name" : "Annexe management on orders for AESA SA",
    "version" : "1.0",
    "author" : "Camptocamp SA",
    "website" : "http://camptocamp.com",
    "depends" : ['sale','product'],
    "category" : "Generic Modules/Projects & Services",
    "description": """
Add the possibility to define options on a product (as a many2many field on product). Those options 
are others related product that could be sold with it. An example would be a computer, and the options could 
be a bag and an additionnal batterie.

Once the options are defined, you can print out a report from the SO (sale order) that include the options
list for the current offer. It'll disyplay the price of each of them  according to the selected pricelist and
could be included in the docs sent to the customer.
""",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "report.xml",
        "c2c_annexe_order_view.xml"
    ],
    "active": False,
    "installable": True
}

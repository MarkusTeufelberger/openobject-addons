# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2008 ChriCar Beteilugungs- und Beratungs- GmbH All Rights Reserved.
#                    Ferdinand Gassauer <tiny@chricar.at>
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
	"name" : "Product GTIN EAN8 EAN13 UPC JPC Support",
	"version" : "1.1",
	"author" : "ChriCar Beteiligungs- und Beratungs- GmbH",
	"website" : "http://www.chricar.at/ChriCar",
	"category" : "Generic Modules/Others",
	"depends" : ["product"],
	"description" : """Replaces the EAN13 code completion with a checkroutine for EAN13, EAN8, JPC, UPC and GTIN
    makes EAN visible in simplified view
        """,
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : ["chricar_product_gtin_view.xml"],
	"active": False,
	"installable": True
}

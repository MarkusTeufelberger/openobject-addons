##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
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
	"name" : "Sale Recent Product",
	"version" : "0.1",
	"description" : """This module adds a new field in sale order lines to allow choosing only the products the partner has ordered sometime in the past. This is useful for companies in which partners tend to ask always the same products but don't know the code or remember the exact model.""",
	"author" : "NaN for Trod y Avia, S.L.",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 'sale' ], 
	"category" : "Custom Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [ 'sale_order_view.xml' ],
	"active": False,
	"installable": True
}

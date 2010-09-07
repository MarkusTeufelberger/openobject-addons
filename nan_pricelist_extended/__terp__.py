# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2009,2010  All Rights Reserved.
#
#   NaN Projectes de programari lliure S.L.
#   http://www.nan-tic.com 
#   author: Àngel Àlvarez  - angel@nan-tic.com 
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
	"name" : "Pricelist Extended",
	"version" : "1.0",
	"description" : """\
Extends pricelist by:
- Adding a category to pricelist items.
- Allowing to accumulate values from several pricelists.
- If a price is not found in a 'based on' pricelist, it will 
  consider it didn't match the current item and move to the next one.

It also allows configuring what kind of rounding happens on pricelists:
- Round to nearest value (default)
- Round up
- Round down
""",
	"author" : "NaN for Trod y Avia, S.L.",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 
		'product'
	], 
	"category" : "Custom Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [
		'pricelist_view.xml',
	],
	"active": False,
	"installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

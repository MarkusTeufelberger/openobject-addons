# -*- coding: utf-8 -*-
##############################################################################
#
# @author Grand-Guillaume Joel
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
     "name" : "Multi-Costs Handling in stock",
     "version" : "1.0",
     "author" : "Camptocamp",
     "category" : "Generic Modules/Accounting",
     "description":
"""
This is improve multi-company into OpenERP regarding to product costs in company. Refer
to c2c_multicost_base description for more infos...

What has been done here:

 * Add price type on company as a property (with default value based on standard price)

 * Stock accounting
  * Use the price type currency and field for cost valuation
  * Into stock move for standard price
  * Into stock move for average price

This module need to be install if you install both stock and c2c_multicost_base.

""",
     "website": "http://camptocamp.com",
     "depends" : [
          "stock",
          "c2c_multicost_base",
                ],
     "init_xml" : [],
     "demo_xml" : [],
     "update_xml" : [
          "multicost_stock_wizard.xml",
     ],
     "active": False,
     "installable": True
}

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
     "name" : "Multi-Costs Handling base",
     "version" : "1.0",
     "author" : "Camptocamp",
     "category" : "Generic Modules/Accounting",
     "description":
"""
This is improve multi-company into OpenERP regarding to product costs in multi-company. It also improve
the multi-currency handling into analytic accounting.

This module (as all c2c_multicost*) is a port to current stable from our work merged in the trunk branch of OpenERP.

What has been done here:

 * Add price type on company as a property (with default value based on standard price)

 * Analytic accounting
  * Use the price type currency and field for cost valuation (including timesheet)
  * Add multi-currency on analytic lines (similar to financial accounting)
  * Allow to share the same product between company employees, with different cost for each one
  * Correct all "costs" indicators into analytic account to base them on the right currency (owner's company)

 * By default, nothing change for single company implementation (base the cost valuation on standard price)

 * Factorise part of function field into analytic accounting

As a result, we can now really share the same product between companies that doesn't have the same currency and/or same cost price. 
We can also manage one field per company on the product form to store the cost for a given price type (and so for a given company).


Warning !! 

This module change some functions signatures in some object. In order to have it running properly,
you need to install every c2c_multicost_*, where * is the name of the already install module.

Example : If you're using hr_expense, then don't forget to install c2c_multicost_expense.
     
""",
     "website": "http://camptocamp.com",
     "depends" : ["account",
                 "account_analytic_analysis",
                 "product",
                ],
     "init_xml" : [],
     "demo_xml" : [],
     "update_xml" : [
          "analytic_view.xml",
          "company_view.xml",
          'product_data.xml',
     ],
     "active": False,
     "installable": True
}

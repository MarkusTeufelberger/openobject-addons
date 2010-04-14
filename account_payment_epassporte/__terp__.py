# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#                       Alejandro Sanchez <alejandro@asr-oss.com>
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
    "name" : "Import ePassporte Payments",
    "version" : "1.0",
    "author" : "Zikzakmedia",
    "description" : """Import ePassporte Payments from a CSV file.

Adds a wizard in bank statements to select a CSV file with ePassporte payments lines like this:

"Transaction Date","Posted Date","Description","Amount in USD","Balance"
3/27/2009,3/27/2009,"b2p Fee",-2.00,17816.06
3/27/2009,3/27/2009,"b2p particularaccount",-11.17,17818.06
3/23/2009,3/24/2009,"b2b Fee",-2.00,17829.23
3/23/2009,3/24/2009,"b2b businessaccount",-111.51,17831.23

Checks if the bank statement currency and ePassporte file currency (USD in the example) are the same.
Tries to fill the partner information from the ePassporte account (businessaccount and particularaccount in the example). This ePassporte account is searched in the partner bank account field (the bank name of ePassporte accounts must be 'EPASSPORTE').
If the 'Search invoice to reconcile' option is checked, tries to reconcile with an open invoice with the same partner, same amount+-accuracy, same date+-accuracy and payment type 'EPASSPORTE'.

First we must define an ePassporte importation configuration:
    * The account for the ePassporte fees.
    * If you want to insert the ePassporte transactions in the bank statement or only show the warning or error messages.
    * If you want to reconcile with open invoices (giving an amount and date accuracy to search the invoices).
""",
    "website" : "www.zikzakmedia.com",
    "license" : "GPL-3",
    "category" : "Generic Modules/Accounting",
    "depends" : ["base", "account", "account_payment_extension"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "epassporte_wizard.xml",
        "epassporte_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable" : True,
    "active" : False,
}

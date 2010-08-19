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
    "name" : "Import Paypal Payments",
    "version" : "1.0",
    "author" : "Zikzakmedia",
    "description" : """Import Paypal Payments from a CSV file.

Adds a wizard in bank statements to select a CSV file with Paypal payments lines like this:

Date, Time, Time Zone, Name, Type, Status, Currency, Gross, Fee, Net, From Email Address, To Email Address, Transaction ID, Counterparty Status, Address Status, Item Title, Item ID, Shipping and Handling Amount, Insurance Amount, Sales Tax, Option 1 Name, Option 1 Value, Option 2 Name, Option 2 Value, Auction Site, Buyer ID, Item URL, Closing Date, Escrow Id, Invoice Id, Reference Txn ID, Invoice Number, Custom Number, Receipt ID, Balance, Address Line 1, Address Line 2/District, Town/City, State/Province/Region/County/Territory/Prefecture/Republic, Zip/Postal Code, Country, Contact Phone Number, 
"25/03/2009", "23:45:35", "GMT+02:00", "Computer Company", "Web Accept Payment Received", "Completed", "EUR", "20,00", "-0,89","19,11", "from1@email.com", "to@email.com","0LN645674B531493M","Non-U.S. - Verified", "Non-U.S.","Item1 title", "1", "0,00","","0,00","usr", "45678","","","","","","","","","","","","","1.315,74", "address1","","city1","state1", "zip1","country1","",
"28/03/2009","21:58:54","GMT+02:00", "John Smith", "Web Accept Payment Received", "Completed", "USD","20,00","-0,94","19,06", "from2@email.com", "to@email.com", "6V823569E37342433", "Verified","Confirmed","Item 2 title","1", "0,00","","0,00","usr", "34567","","","", "","","","","","","","","", "20.979,99", "address2","", "city2","state2","zip2","country2","",

These fields are optional: Address Line 1, Address Line 2/District, Town/City, State/Province/Region/County/Territory/Prefecture/Republic, Zip/Postal Code, Country, Contact Phone Number.

Only the Paypal payment lines with the same currency as the bank statement are imported. And if 'Status completed' option is checked, only the Paypal payment lines with status field = 'Completed' are imported.

Paypal transactions are classified as:
    * customer: 'Type' in ['Web Accept Payment Received', 'Payment Received', 'Subscription Payment Received', 'Refund']
    * supplier: 'Type' in ['Credit']
    * general: Other cases, 'Type' in ['Transfer', 'Chargeback Settlement', ...]

Tries to fill the partner and invoice to conciliate from the Paypal transaction ID. If not, try to find the partner with the from (customer) or to (supplier) email addresses (from1@email.com or to@email.com in the example) and, if the 'Search invoice to reconcile' option is checked, try to conciliate it with an open invoice with the same partner, same amount+-accuracy, same date+-accuracy and payment type 'PAYPAL'.

The from/to Paypal email address (it can be considered as a Paypal account) is searched in the partner bank account field (the bank name of Paypal accounts must be 'PAYPAL').

First we must define a Paypal importation configuration:
    * The account for the Paypal fees.
    * If you want to insert the Paypal transactions in the bank statement or only show the warning or error messages.
    * If you want to reconcile with open invoices (giving an amount and date accuracy to search the invoices).
""",
    "website" : "www.zikzakmedia.com",
    "license" : "GPL-3",
    "category" : "Generic Modules/Accounting",
    "depends" : ["base", "account", "account_payment_extension"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "paypal_view.xml",
        "paypal_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "installable" : True,
    "active" : False,
}

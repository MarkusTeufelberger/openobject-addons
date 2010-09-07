# -*- coding: utf-8 -*-
{
     "name"         : "ChriCar Account Analytic",
     "version"      : "0.1",
     "author"       : "ChriCar Beteiligungs- und beratungs GmbH",
     "website"      : "http://www.chricar.at/ChriCar",
     "description"  : """WORK IN PROGRESS
     Allows to define analytic accounts and their usage for accounts
     It is especially IMPORTANT to assign default analytic accounts to all P&L accounts
       which are created automatically

checks implemented
main - will check/prohibit everything what comes in wrong from other modules
./account/account_move_line.py

other checks implemented
./account/account_bank_statement.py
./account/invoice.py

potentialy important
./purchase/purchase.py
./sale/sale.py

other  - naming !!!
* analytic_account_id
./account_analytic_plans/account_analytic_plans.py
./account_budget/crossovered_budget.py
./c2c_budget/c2c_budget_line.py
./report_timesheet/report_timesheet.py
* account_analytic_id
./account_asset/account_asset.py
./account_voucher/voucher.py
./auction/auction.py
       """,
     "category"     : "Client Modules/ChriCar Addons",
     "depends"      : ["base","account"],
     "init_xml"     : [],
     "demo_xml"     : [],
     "update_xml"   : ["account_analytic_view.xml"],
     "active"       : False,
     "installable"  : True
}


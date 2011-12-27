# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    "name" : "Account Fiscal Position Rules for Canada",
    "version" : "0.1",
    "author" : "Savoir-faire Linux",
    "website" : "http://www.savoirfairelinux.com",
    "license" : "AGPL-3",
    "category" : "Localization/Accounting",
    "description": """This module adds the fiscal position rules to set the 
    fiscal position of a partner based on the canadian province or territory.
    """,
    "depends" : ['account_fiscal_position_rule','l10n_ca_toponyms','l10n_ca'],
    "init_xml" : [],
    "update_xml" : ['rules.xml'],
    "demo_xml" : [],
    "installable" : True,
    "certificate" : ''
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


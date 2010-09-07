# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
    "name" : "Authenticate users with ldap server",
    "version" : "0.2",
    "depends" : ["base"],
    "author" : "Tiny",
    "description": """Add support for authentication by ldap server
If authentification succefull, it check if the user exists on the database, otherwise it is created

    !!!WORK ONLY WITH LDAP NOT LDAPS !!! """,
    "website" : "http://www.openerp.com",
    "category" : "Generic Modules/Others",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "users_ldap_view.xml",
    ],
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

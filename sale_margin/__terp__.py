# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_margin module for OpenERP, add margin in sale order and invoice
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2009 EVERLIBRE (<http://www.Everlibre.fr>) Éric VERNICHON
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
#
#    This file is a part of sale_margin
#
#    sale_margin is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_margin is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name":"Margins (amount and pourcent) in Sale Orders",
    "description" : " This module adds the facility of Margins (amount and pourcent) in Sale Orders",
    "version":"1.0",
    "author":"Everlibre & SYLEAM",
    "category" : "Generic Modules/Sales & Purchases",
    "depends":[
        "base",
        "sale",
        "account"
    ],
    "demo_xml":[],
    "update_xml":[
        "security/ir.model.access.csv",
        "view/sale_margin_view.xml",
        "view/report_margin_view.xml",
    ],
    "active": False,
    "installable": True,
    "license": "GPL-3",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

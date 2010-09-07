# -*- coding: utf-8 -*-
##############################################################################
#
#    purchase_price_update module for OpenERP, Updates prices in purchase when pricelist is changed
#    Copyright (C) 2010 INVITU SARL (<http://www.invitu.com/>)
#              nobody <support@invitu.com>
#
#    This file is a part of purchase_price_update
#
#    purchase_price_update is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    purchase_price_update is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Purchase Price Update',
    'version': '0.1.0',
    'category': 'Custom',
    'description': """Updates prices in purchase when pricelist is changed""",
    'author': 'INVITU SARL',
    'website': 'http://www.invitu.com/',
    'depends': [
        'base',
        'purchase',
        ],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

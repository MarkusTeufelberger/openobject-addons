# -*- encoding: utf-8 -*-
##############################################################################
#
#    This module is copyright (C) 2009 Numérigraphe SARL. All Rights Reserved.
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
    'name' : 'Set fixed delivery dates on Sale Orders ***NEEDS PATCHING***',
    'version' : '0.1',
    'author' : u'Numérigraphe',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """This module lets you specify the date when the Customers\
want Sale Orders delivered.

WARNING! the official standard sale module does not easily \
allow other modules to redefine the way the delivery date are computed. This \
module was written against a patched version of the sale module that makes it \
possible.
The patch is included in the "patch" directory of this module's source code.""",
    'depends' : [
                 'base',
                 'sale',
                 ],
    'init_xml' : [
                  ],
    'demo_xml' : [
                  'test/sale_delivery_date_test.xml'
                  ],
    'update_xml' : [
                    'sale_view.xml',
                    ],
    'active': False,
    'installable': True,
    'license' : 'GPL-3',
}

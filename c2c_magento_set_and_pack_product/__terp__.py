# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Joël Grand-Guillaume and Guewen Baconnier. Copyright Camptocamp SA
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
    'name' : 'c2c_magento_set_and_pack_product',
    'version' : '1',
    'depends' : ['base', 'product', 'magentoerpconnect', 'c2c_magento_product_components'],
    'author' : 'Camptocamp',
    'description': """Management of products for Magento: 
Define in a Magento's attribute if the product is : 
 - a normal product
 - a pack (Phantom BoM)
 - a set (Normal BoM)
The name of the attribute to synchronize with Magento is defined in settings/external.mappinglines.template.csv
Needs customization in Magento which define how to handle each type of product. 
""",
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': ['product_view.xml', 
                   'settings/external.mappinglines.template.csv'
                  ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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
    'name' : 'c2c_magento_shipping',
    'version' : '1',
    'depends' : ['base', 'stock', 'base_sale_multichannels', 'magentoerpconnect', ],
    'author' : 'Camptocamp',
    'description': """Customisation of the Magento ERP Connector module for the shippings.
 - The signature of the Magento's method sales_order_shipment.create is modified to send the modified products and their quantity
 - Inform Magento if a packing is the last one
 - Send the packings in the right order from first to last
 - Remove the components of a bills of materials in an sale order if their price is 0.0. 

Works with a Magento customisation to handle shippings the same way!

The magento method sales_order_shipment.create is modified to handle the product changement and the "last packing" information.
It sends the pack and its components with a 0.0 price because it needs to have all the products in the sale order in order to have correct shipments.

""",
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

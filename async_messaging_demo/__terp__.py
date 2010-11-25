# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai (gdukai@gmail.com)
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
    'name': 'Asynchronous Messaging Demo Application',
    'version': '1.0',
    'author': 'Gábor Dukai',
    'website' : 'http://exploringopenerp.blogspot.com',
    'category': 'Generic Modules',
    'description': """
    A demo application that you can use to send and receive STOMP messages
    with OpenERP. It can send text messages and OpenERP objects, too.
    Objects sent will be created in the receiving instance.

    The recipient could be the same database from which you sent the message
    or any other. It's easy to set up brokers to reliably deliver
    messages in heterogenous and unrealiable networks.

    Try it with ActiveMQ <http://activemq.apache.org/>, a default install
    should do.

    Compatibility: tested with OpenERP v5.0
    """,
    'depends': ['async_messaging'],
    'init_xml': [],
    'update_xml': [
        'demo_view.xml',
    ],
    'demo_xml': [],
    'license': 'GPL-3',
    'installable': True
}
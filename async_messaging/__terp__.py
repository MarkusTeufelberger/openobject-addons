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
    'name': 'Asynchronous Messaging with STOMP Base Module',
    'version': '1.01',
    'author': 'Gábor Dukai',
    'website' : 'http://exploringopenerp.blogspot.com',
    'category': 'Generic Modules',
    'description': """
    This module should be used for building integration solutions based on
    messaging patterns.
    It provides:
      - A framework for sending and receiving STOMP messages.
      - A serializator/deserializator that creates and reads an XML
      representation of any OpenERP object.
      - stomppy 3.0.2a is included from http://code.google.com/p/stomppy/

    This module is based on Cloves J. G. de Almeida's <cjalmeida@gvmail.br>
    mbi module, especially the XML serializator that was just copied here.

    Compatibility: tested with OpenERP v5.0
      and ActiveMQ 5.4.1 http://activemq.apache.org/
    """,
    'depends': ['base'],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'company_view.xml',
        'scheduler_data.xml',
    ],
    'demo_xml': [],
    'license': 'GPL-3',
    'installable': True
}
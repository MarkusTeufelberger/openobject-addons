# -*- encoding: utf-8 -*-
##############################################################################
#
#    ETL system- Extract Transfer Load system
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
"""
 To provide connectivity with XMLRPC Server.

 Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
 GNU General Public License.
"""
import threading
from etl.connector import connector


class xmlrpc_server_thread(threading.Thread):
    _register_functions = []

    def register_functions(self, funs):
        if not self._register_functions:
            self._register_functions = []
        if isinstance(funs,list):
            self._register_functions += funs
        else:
            self._register_functions.append(funs)

    def get_register_functions(self):
        return self._register_functions

    def run(self):
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
        server = SimpleXMLRPCServer((self.host, self.port))
        server.register_introspection_functions()
        for fun in self.get_register_functions():
            server.register_function(fun)
        server.serve_forever()
        return server

class xmlrpc_connector(connector):
    """
    This is an ETL connector that provides connectivity with xmlrpc server.
    """

    def __init__(self, host, port, name='xmlrpc_connector'):
        """
        Initializes the parameters required to connect to xmlrpc server.
        """
        super(xmlrpc_connector, self).__init__(name)
        self._type = 'connector.xmlrpc_connector'
        self.host = host
        self.port = port

    def __getstate__(self):
        res = super(xmlrpc_connector, self).__getstate__()
        res.update({'host':self.host, 'port':self.port})
        return res

    def __setstate__(self, state):
        super(xmlrpc_connector, self).__setstate__(state)
        self.__dict__ = state

    def start(self,funs):
        xml_server = xmlrpc_server_thread()
        xml_server.host = self.host
        xml_server.port = self.port
        xml_server.register_functions(funs)
        server = xml_server.start()

    def connect(self):
        import xmlrpclib
        server = xmlrpclib.ServerProxy('http://' + self.host + ':' + str(self.port))
        return server

    def __copy__(self):
        """
        Overrides copy method.
        """
        res = xmlrpc_connector(self.host, self.port)
        return res

def test():
    """
    Test function.
    """
    #TODO
    from etl_test import etl_test
    import etl
    xmlrpc_conn=xmlrpc_connector('localhost',8050)
    conn = xmlrpc_conn.start('import_data')
    test = etl_test.etl_component_test(etl.component.input.xmlrpc_in( etl.component.input.xmlrpc_in(xmlrpc_conn)))
    res=test.output()
    print res

if __name__ == '__main__':
    test()


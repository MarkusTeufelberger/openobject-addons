#!/usr/bin/python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
import etl
import tools
from osv import osv, fields

class etl_component_xml_in(osv.osv):
    _name='etl.component'
    _inherit = 'etl.component'
    _columns = {
        'xml_params': fields.char('XML Parameters', size=64),
     }

    def create_instance(self, cr, uid, id, context={}, data={}):
        val = super(etl_component_xml_in, self).create_instance(cr, uid, id, context, data)
        obj_connector = self.pool.get('etl.connector')
        obj_transformer = self.pool.get('etl.transformer')
        cmp=self.browse(cr, uid, id)
        if cmp.type_id.name == 'input.xml_in':
            conn_instance=trans_instance = False
            if cmp.connector_id:
                conn_instance=obj_connector.get_instance(cr, uid, cmp.connector_id.id, context, data)
            if cmp.transformer_id:
                trans_instance=obj_transformer.get_instance(cr, uid, cmp.transformer_id.id, context, data)

            val =etl.component.input.xml_in(conn_instance, 'component.input.xml_in', trans_instance, cmp.row_limit, cmp.xml_params and eval(cmp.xml_params) or {})
        return val

etl_component_xml_in()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
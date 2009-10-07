# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Sharoon Thomas, Raphael Valyi
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

from osv import fields, osv

class external_osv(osv.osv):
    def extid_to_oeid(self, cr, uid, ids, external_referential_id):
        #First get the external key field name
        #conversion external id -> OpenERP object using Object mapping_column_name key!
        mapping_id = self.pool.get('external.mapping').search(cr, uid, [('model', '=', self._name), ('referential_id', '=', external_referential_id)])
        if mapping_id:
            #now get the external field name
            ext_field_name = self.pool.get('external.mapping').read(cr, uid, mapping_id[0], ['external_field'])['external_field']
            if ext_field_name:
                #now get the oe_id
                oe_id = self.search(cr, uid, [(ext_field_name, '=', ids)])
                if oe_id:
                    return oe_id[0]
                

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L.
#                       (http://www.nan-tic.com) All Rights Reserved.
#
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import time
import base64
import tempfile
from osv import osv
from osv import fields
from tools.translate import _
from tools import convert

class base_module_record_set(osv.osv):
    _name = 'base.module.record.set'

    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'model_ids': fields.many2many('ir.model', 'ir_model_base_module_record_set_rel', 'set_id', 'model_id', 'Models', help='Models that will be stored when a backup is created.'),
        'backup_ids': fields.one2many('base.module.record.set.backup', 'set_id', 'Backups', help='List of backups created from this set.'),
    }

    def action_create_backup(self, cr, uid, ids, context):
        user = self.pool.get('res.users').browse(cr, uid, uid, context).login
        for record_set in self.browse(cr, uid, ids, context):
            model_ids = []
            self.pool.get('ir.module.record').recording_data = []

            for model in record_set.model_ids:
                model_ids.append( model.id )
                for id in self.pool.get(model.model).search(cr, uid, [], context=context):
                    args=(cr.dbname, uid,user, model.model,'copy_with_ids', id, {}, context)
                    self.pool.get('ir.module.record').recording_data.append(('query', args, {}, id))
                #data_ids = self.pool.get(model.model).search(cr, uid, [], context=context)
                #args=(cr.dbname, uid,user, model.model,'copy_with_ids', data_ids, {}, context)
                #self.pool.get('ir.module.record').recording_data.append(('query', args, {}, id))

            # Let the system automatically create ir.model.data IDs for those records that do not have one.
            # This way, restoring to the current database will not create duplicated entries.
            ctx = context.copy()
            ctx['import_compatible'] = True
            xml = self.pool.get('ir.module.record').generate_xml(cr, uid, ctx)

            self.pool.get('base.module.record.set.backup').create(cr, uid, {
                'set_id': record_set.id,
                'model_ids': [(6,0,model_ids)],
                'xml': base64.encodestring( xml ),
            }, context)
        return False

base_module_record_set()

class base_module_record_set_backup(osv.osv):
    _name = 'base.module.record.set.backup'

    _columns = {
        'set_id': fields.many2one('base.module.record.set', 'Set', required=True, ondelete='cascade'),
        'timestamp': fields.datetime('Timestamp', required=True, help='Date & time when this backup was created.'),
        'name': fields.char('Name', size=256, required=True, help='Descriptive name given to this backup.'),
        'model_ids': fields.many2many('ir.model', 'ir_model_base_module_record_set_backup_rel', 'set_backup_id', 'model_id', 'Models', help='Models used to create this backup.'),
        'xml': fields.binary('XML', filters=['*.xml'], help='XML backup file.'),
    }
    _defaults = {
        'timestamp': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'name': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    def restore(self, cr, uid, ids, remove_existing_records, context):
        start = time.strftime('%Y-%m-%d %H:%M:%S')
        for backup in self.browse(cr, uid, ids, context):
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write( base64.decodestring( backup.xml ) )
            f.close()
            convert.convert_xml_import(cr, 'nan_base_module_record_extension', f.name)
            os.unlink( f.name )

            if not remove_existing_records:
                continue

            for model in backup.model_ids:

                object_in_pool = self.pool.get(model.model)
                if '_log_access' in dir( object_in_pool ):
                    if not (object_in_pool._log_access):
                        search_condition=[]
                    if '_auto' in dir(object_in_pool):
                        if not object_in_pool._auto:
                            continue

                filter = [('create_date','<',start),('write_date','=',False)]
                old_ids = object_in_pool.search(cr, uid, filter, context=context)
                
                filter = [('write_date','!=',False),('write_date','<',start)]
                old_ids += object_in_pool.search(cr, uid, filter, context=context)

                object_in_pool.unlink(cr, uid, old_ids, context)
        

    def action_restore(self, cr, uid, ids, context):
        self.restore(cr, uid, ids, False, context)
        return False

    def action_restore_and_remove(self, cr, uid, ids, context):
        self.restore(cr, uid, ids, True, context)
        return False

base_module_record_set_backup()

class base_module_record(osv.osv):
    _inherit = 'ir.module.record'

    def _get_id(self, cr, uid, model, id, context):
        if context is None:
            context = {}
        result = super(base_module_record, self)._get_id(cr, uid, model, id, context)
        if result == (None, None) and context.get('import_compatible', False):
            data = self.pool.get( model ).read(cr, uid, [id], ['name'], context)[0]
            name = self._create_id(cr, uid, model, data, context)
            module = 'nan_base_module_record_extension'
            noupdate = False

            number = ''
            while True:
                data_ids = self.pool.get('ir.model.data').search(cr, uid, [
                    ('module','=',module),
                    ('name','=',name + number)
                ], context=context)
                if not data_ids:
                    name = name + number
                    break
                number = str( int(number or '0') + 1 )

            model_data_id = self.pool.get('ir.model.data').create(cr, uid, {
                'name': name,
                'noupdate': noupdate,
                'res_id': id,
                'model': model,
                'module': module,
            }, context)
            result = module + '.' + name, noupdate
            self.depends[module] = True
        return result
        
    def _generate_object_xml(self, cr, uid, rec, recv, doc, result=None, context=None):
        record_list = []
        noupdate = False
        if rec[4] == 'copy_with_ids':
            data=self.get_copy_data(cr, uid, rec[3], rec[5], rec[6], context)

            id, update = self._get_id(cr, uid, rec[3], rec[5], context)
            noupdate = noupdate or update

            record,noupdate = self._create_record(cr, uid, doc, rec[3], rec[6], id, context=context)
            self.ids[(rec[3], result)] = id
            record_list += record
                                                                                                            
            return record_list, noupdate
        return super(base_module_record, self)._generate_object_xml(cr, uid, rec, recv, doc, result, context)

base_module_record()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

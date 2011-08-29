# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import netsvc
import pooler
import time
import urllib
import base64
from osv import osv

def export_table(self, cr, uid, data, context, server, table, fields, filter = [], filterphp = ''):
    """Export (synchronize) the fields of the radiotv.table to Joomla PHP server.
       Only the records matching the filter are exported.
       filterphp is the same filter in SQL notation to used in the PHP code.
       New records are inserted, existing records are updated and removed records are deleted"""
    pool = pooler.get_pool(cr.dbname)
    obj = 'radiotv.'+table
    tbl = 'radiotv_'+table
    new = 0
    update = 0
    server.reset_table(tbl)
    elem_ids = pool.get(obj).search(cr, uid, filter)
    for elem in pool.get(obj).browse(cr, uid, elem_ids, context):
        vals = {}
        for field in fields:
            if field[-3:] == "_id":
                vals[field] = getattr(elem, field).id
            elif field[-4:] == "_ids":
                vals[field] = [c.id for c in getattr(elem, field)]
            else:
                vals[field] = getattr(elem, field)

        attach_ids = pool.get('ir.attachment').search(cr, uid, [('res_model','=',obj), ('res_id', '=',elem.id)])
        cont = 0
        for data in pool.get('ir.attachment').browse(cr, uid, attach_ids, context):
            if data['type'] == 'binary':
                s = data['datas_fname'].split('.')
                extension = s[-1].lower()
                s.pop()
                name = ".".join(s)
                if extension in ['jpeg', 'jpe', 'jpg', 'gif', 'png']:
                    if extension in ['jpeg', 'jpe', 'jpg']:
                        extension='jpeg'
                    vals['picture'+str(cont)] = data['datas']
                    vals['fname'+str(cont)] = name + '.' + extension
            else:
                all_url = data['url'].split('/')
                s = all_url[-1].split('.')
                extension = s[-1].lower()
                s.pop()
                name = ".".join(s)
                if extension in ['jpeg', 'jpe', 'jpg', 'gif', 'png']:
                    if extension in ['jpeg', 'jpe', 'jpg']:
                        extension='jpeg'
                    try:
                        vals['picture'+str(cont)] = base64.encodestring(urllib.urlopen(data['url']).read())
                    except:
                        continue
                    vals['fname'+str(cont)] = name + '.' + extension
            cont = cont + 1
        if server.set_table(tbl, vals):
            new += 1
        else:
            update += 1
    delete = server.delete_table(tbl, filterphp)
    return (new, update, delete)


def export_write(self, cr, uid, server, table, ids, vals, context):
    """Synchronize the fields defined in vals of the radiotv.table to Joomla PHP server.
       Only the records with ids are exported.
       New records are inserted, existing records are updated"""
    pool = pooler.get_pool(cr.dbname)
    obj = 'radiotv.'+table
    tbl = 'radiotv_'+table
    new = 0
    update = 0
    for field in vals.keys():
        if field[-4:] == "_ids":
            vals[field] = vals[field][0][2]
    for id in ids:
        vals['id'] = id
        attach_ids = pool.get('ir.attachment').search(cr, uid, [('res_model','=',obj), ('res_id', '=',id)])
        cont = 0
        for data in pool.get('ir.attachment').browse(cr, uid, attach_ids, context):
            if data['type'] == 'binary':
                s = data['datas_fname'].split('.')
                extension = s[-1].lower()
                s.pop()
                name = ".".join(s)
                if extension in ['jpeg', 'jpe', 'jpg', 'gif', 'png']:
                    if extension in ['jpeg', 'jpe', 'jpg']:
                        extension='jpeg'
                    vals['picture'+str(cont)] = data['datas']
                vals['fname'+str(cont)] = name + '.' + extension
            else:
                all_url = data['url'].split('/')
                s = all_url[-1].split('.')
                extension = s[-1].lower()
                s.pop()
                name = ".".join(s)
                if extension in ['jpeg', 'jpe', 'jpg', 'gif', 'png']:
                    if extension in ['jpeg', 'jpe', 'jpg']:
                        extension='jpeg'
                    try:
                        vals['picture'+str(cont)] = base64.encodestring(urllib.urlopen(data['url']).read())
                    except:
                        continue
                vals['fname'+str(cont)] = name + '.' + extension
            cont = cont + 1
        if server.set_table(tbl, vals):
            new += 1
        else:
            update += 1

    return (new, update)


def export_ulink(self, cr, uid, server, table, ids, table_rel=None, field_rel=None):
    """Synchronize the radiotv.table to Joomla PHP server.
       Only the records with ids are deleted.
       If table_rel and field_rel are defined, also deletes the records in the table_rel"""
    tbl = 'radiotv_'+table
    delete = server.delete_items(tbl, ids, "id")
    if table_rel != None:
        tbl = 'radiotv_'+table_rel
        server.delete_items(tbl, ids, field_rel)
    return delete

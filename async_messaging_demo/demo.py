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

from lxml import etree

from osv import osv, fields
from async_messaging.async_messaging import STOMPListener

class async_messaging_demo(osv.osv):
    _name = 'async.messaging.demo'

    _columns = {
        'name': fields.char('Name', size=64),
        'destination_ids': fields.one2many('async.messaging.demo.destination',
            'demo_id', 'Send To'),
        'log': fields.text('Received Messages Log'),
    }

    def send_message(self, cr, uid, ids, msg):
        mbi_obj = self.pool.get('mbi')
        destinations = []
        for demo in self.browse(cr, uid, ids):
            for dst in demo.destination_ids:
                destinations.append(dst.name + '/demo')
        mbi_obj.send(cr, uid, msg, destinations)

    def create_and_send_text_message(self, cr, uid, ids, text):
        doc = etree.Element('message')
        doc.set('type', 'text')
        doc.text = (text or '')
        msg = etree.tostring(doc, pretty_print=True,
                encoding='utf-8', xml_declaration=True)
        self.send_message(cr, uid, ids, msg)

    def create_and_send_object_message(self, cr, uid, ids, obj_name,
        xml_bindings, obj_ids):
        doc = etree.Element('message')
        doc.set('type', 'create')
        obj = self.pool.get(obj_name)
        doc.extend(obj.obj_to_xml(cr, uid, obj_ids, obj_name, xml_bindings))
        msg = etree.tostring(doc, pretty_print=True,
            encoding='utf-8', xml_declaration=True)
        self.send_message(cr, uid, ids, msg)

async_messaging_demo()

class async_messaging_demo_destination(osv.osv):
    _name = 'async.messaging.demo.destination'
    _description = 'Send To'

    _columns = {
        'name': fields.char('DB Name', size=64, required=True,
            help='Database name of an OpenERP instance running async messaging demo.'),
        'demo_id': fields.many2one('async.messaging.demo', 'Demo', required=True),
    }

    def create(self, cr, uid, vals, context=None):
        res = super(async_messaging_demo_destination, self)\
            .create(cr, uid, vals, context=context)
        mbi_obj = self.pool.get('mbi')
        mbi_obj.setup_sending_agents(cr, uid)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(async_messaging_demo_destination, self)\
            .write(cr, uid, ids, vals, context=context)
        mbi_obj = self.pool.get('mbi')
        mbi_obj.setup_sending_agents(cr, uid)
        return res

async_messaging_demo_destination()

class async_messaging_demo_text(osv.osv_memory):
    _name = 'async.messaging.demo.text'

    _columns = {
        'text': fields.text('Text'),
    }

    def action_send(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        demo_obj = self.pool.get('async.messaging.demo')
        demo_obj.create_and_send_text_message(cr, uid, context['active_ids'],
            wiz.text)
        self.write(cr, uid, ids, {'text': ''})
        return True

async_messaging_demo_text()

class async_messaging_demo_object(osv.osv_memory):
    _name = 'async.messaging.demo.object'

    _columns = {
        'model_id': fields.many2one('ir.model', 'Object', required=True),
        'field_ids': fields.many2many('ir.model.fields', 'demo_field_rel',
            'wizard_ids', 'field_ids', 'Fields', required=True,
            domain="[('model_id','=',model_id)]"),
        'object_id_list': fields.char('Object ID List', size=32, required=True,
            help="Comma separated ID numbers.")
    }

    def action_send(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        demo_obj = self.pool.get('async.messaging.demo')
        xml_bindings = []
        for field in wiz.field_ids:
            xml_bindings.append((field.name, field.name))
        demo_obj.create_and_send_object_message(cr, uid, context['active_ids'],
            wiz.model_id.model, xml_bindings, wiz.object_id_list.split(','))
        self.write(cr, uid, ids, {'object_id_list': False})
        return True

async_messaging_demo_object()

class DemoListener(STOMPListener):
    def __init__(self, pool, dbname, uid):
        self.demo_obj = pool.get('async.messaging.demo')
        super(DemoListener, self).__init__(pool, dbname, uid)

    def process_message(self, cr, uid, doc):
        def _log_to_user(text):
            demo_ids = self.demo_obj.search(cr, uid, [])
            for demo in self.demo_obj.browse(cr, uid, demo_ids):
                self.demo_obj.write(cr, uid, [demo.id],
                    {'log': (demo.log or '') + text})
        if doc.get('type') == 'text':
            text = 'Text message processed: \n' + str(doc) + '\n'
        elif doc.get('type') == 'create':
            text = 'Object message processed: \n'
            try:
                for obj_xml in doc.iterchildren():
                    xml_bindings = [f.tag for f in obj_xml.iterchildren()]
                    obj = self.pool.get(obj_xml.tag)
                    vals = obj.xml_to_vals(cr, uid, obj_xml, xml_bindings, 'create')[2]
                    self.log.debug("consume object: (create, %s)" % str(vals[False]))
                    res = obj.create(cr, uid, vals[False])
                    vals.pop(False)
                    context = {}
                    for lang, data in vals.iteritems():
                        if not data:
                            continue
                        context['lang'] = lang
                        self.log.debug("consume_object: (create, %s, %s)" % (str(data), str(context)))
                        obj.write(cr, uid, [res], data, context)
                    text += 'Object ' + obj_xml.tag + ' created with ID '\
                        + str(res) + '\n'
            except Exception, e:
                #suppress exceptions because we don't want to deal with
                #faulty messages in a demo application
                self.log.debug(str(e))
                raise e
        _log_to_user(text)

class mbi(osv.osv):
    _inherit = 'mbi'

    def get_listeners(self, cr, uid):
        res = super(mbi, self).get_listeners(cr, uid)
        res['demo'] = DemoListener(self.pool, cr.dbname, uid)
        return res

    def get_queues_to_send(self, cr, uid):
        res = super(mbi, self).get_queues_to_send(cr, uid)
        dst_obj = self.pool.get('async.messaging.demo.destination')
        dst_ids = dst_obj.search(cr, uid, [])
        for dst in dst_obj.browse(cr, uid, dst_ids):
            res[dst.name + '/demo'] = True
        return res

mbi()
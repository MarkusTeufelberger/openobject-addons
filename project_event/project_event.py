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
import time

from osv import fields, osv
import pooler
import tools
from tools.config import config
from tools.translate import _
import netsvc


class project_project(osv.osv):
    _inherit = "project.project"
    _columns = {
        "event_ids": fields.one2many('project.event', 'project_id', 'Events', readonly=True),
        "event_configuration_ids": fields.one2many('project.event.configuration', 'project_id', 'Event Configuration'),
    }

    def _log_event(self, cr, uid, project_id, values={}, context={}):
        values['project_id'] = project_id
        if type(project_id) == type([]):
            values['project_id'] = project_id[0]
        self.pool.get('project.event').create(cr, uid, values, context)

project_project()

class project_event_type(osv.osv):
    _name = "project.event.type"
    _columns = {
        'name': fields.char('Name',size=64, required=True),
        'code': fields.char('Code',size=64, required=True)
    }

project_event_type()

def _links_get(self, cr, uid, context={}):
    obj = self.pool.get('project.event.type')
    ids = obj.search(cr, uid, [])
    res = obj.read(cr, uid, ids, ['code', 'name'], context)
    return [(r['code'], r['name']) for r in res]

class project_event(osv.osv):
    _name = "project.event"
    _columns = {
        'name': fields.char('Events', size=64, required=True),
        'description': fields.text('Description'),
        'res_id': fields.integer('Resource Id'),
        'project_id': fields.many2one('project.project', 'Project', select=True, required=True),
        'date': fields.datetime('Date', size=16),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'action' : fields.selection([('create','Create'),('write','Modify'),('unlink','Remove')], 'Action', required=True),
        'type': fields.selection(_links_get, 'Type of Event', required=True),
    }
    _order = 'date desc'
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    def create(self, cr, uid, values, *args, **kwargs):
        attach = False
        new_values = {}
        for key in values:
            if key != 'attach':
                new_values[key] = values[key]
        event_id = super(project_event, self).create(cr, uid, new_values, *args, **kwargs)
        cr.commit()
        project_id = values.get('project_id',False)
        if project_id:
            obj_configuration = self.pool.get('project.event.configuration')
            config_ids = obj_configuration.search(cr, uid, [('project_id','=',project_id)])
            obj_configuration.run(cr, uid, config_ids, values)

project_event()

class project_event_configuration(osv.osv):
    _name = "project.event.configuration"
    _columns = {
        'name': fields.char('Name',size=64, required=True),
        'project_id': fields.many2one('project.project', 'Project', select=True, required=True),
        'create' :fields.boolean('On Create'),
        'write' :fields.boolean('On Write'),
        'unlink' :fields.boolean('On Delete'),
        'type': fields.selection(_links_get, 'Type of Event', required=True),
        'action_type': fields.selection([('email','Email'),('sms','SMS'),('request','Request')], 'Action Type', required=True),
    }
    _defaults = {
        'action_type': lambda *a: 'email',
    }

    def send_mail(self, to_address, subject, body, attach=None):
        sent = tools.email_send(config['email_from'], to_address, subject, body, attach=attach, ssl=True)
        logger = netsvc.Logger()
        if not sent:
            logger.notifyChannel('email', netsvc.LOG_ERROR, 'Failed to send email to : %s' % (to_address))
        else:
            logger.notifyChannel('email', netsvc.LOG_INFO, 'Email successfully send to : %s' % (to_address))

    def run(self, cr, uid, ids, values, context={}):
        for config in self.browse(cr, uid, ids, context=context):
            if values.get('action',False) and config[values['action']] and config.type == values.get('type',False):
                action_to = []
                for member in config.project_id.members:
                    if member.address_id and member.address_id.email:
                        action_to.append(member.address_id.email)
                if config.action_type == 'email' and len(action_to):
                    action = ''
                    if config.create:
                        action = 'New'
                    elif config.write:
                        action = 'Modified'
                    elif config.unlink:
                        action = 'Deleted'
                    subject = '[%s] %s - %d : %s ' %(config.project_id.name, config.type, values.get('res_id',False), values.get('name',False))
                    body = values.get('description',False)
                    self.send_mail(action_to, subject, body, attach=values.get('attach',False))
                elif config.action_type == 'sms':
                    #TODO
                    pass
                elif config.action_type == 'request':
                    #TODO
                    pass

project_event_configuration()

class project_task(osv.osv):
    _inherit = 'project.task'

    def create(self, cr, uid, values, context={}):
        res = super(project_task, self).create(cr, uid, values, context=context)
        cr.commit()
        task = self.browse(cr, uid, res, context=context)
        if task.project_id:
            desc = ''' Hello, \n \t The new task is created for the Project: %s \n\n And its Details are: \n \n Task: %s \n Created on: %s \n Assigned to: %s \n Deadline: %s \n Planned hours: %s \n Remaining hours: %s \n Total Hours: %s \n For Partner: %s \n Task Summary: \n ====== \n %s \n \n ======= \n \nThanks,\nProject Manager \n%s''' \
                       %(task.project_id.name,\
                         task.name, task.date_start, task.user_id.name, \
                         task.date_deadline or '', task.planned_hours or 0, \
                         task.remaining_hours or 0, task.total_hours or 0,\
                         task.partner_id and task.partner_id.name or '',\
                         task.description or '',task.project_id.manager and task.project_id.manager.name or '')
            self.pool.get('project.project')._log_event(cr, uid, task.project_id.id, {
                                'res_id' : task.id,
                                'name' : task.name,
                                'description' : desc,
                                'user_id': uid,
                                'action' : 'create',
                                'type' : 'task'})
        return res

    def write(self, cr, uid, ids, vals, context={}):
        if not isinstance(ids, list):
            ids = [ids]
        task = self.browse(cr, uid, ids)[0]
        res = super(project_task, self).write(cr, uid, ids, vals, context={})
        cr.commit()
        task_data = self.browse(cr, uid, ids[0], context)
        desc = '''Hello ,\n\n  The task is updated for the project: %s\n\nModified Datas are:\n''' %(str(task.project_id.name),)
        for val in vals:
            if val.endswith('id') or val.endswith('ids'):
                continue
            desc += val + ':' + str(vals[val]) + "\n"
        desc += '\nThanks,\n' + 'Project Manager\n' + (task_data.project_id.manager and task_data.project_id.manager.name) or ''
        self.pool.get('project.project')._log_event(cr, uid, task.project_id.id, {
                                                                'res_id' : ids[0],
                                                                'name' : task.name or '',
                                                                'description' : desc,
                                                                'user_id': uid,
                                                                'action' : 'write',
                                                                'type' : 'task'})
        return res

project_task()

class document_file(osv.osv):
    _inherit = 'ir.attachment'

    def create(self, cr, uid, values, *args, **kwargs):
        res = super(document_file, self).create(cr, uid, values, *args, **kwargs)
        cr.commit()
        document = self.browse(cr, uid, res)
        if document.file_size >= 1073741824:
                size = str((document.file_size) / 1024 / 1024 / 1024) + ' GB'
        elif document.file_size >= 1048576:
            size = str((document.file_size) / 1024 / 1024) + ' MB'
        elif document.file_size >= 1024:
            size = str((document.file_size) / 1024) + ' KB'
        elif document.file_size < 1024:
            size = str(document.file_size) + ' bytes'

        if document.res_model == 'project.project' and document.res_id:
            desc = ''' Hello, \n \n \t The new document is uploaded on the Project: %s \n\n Document attached: %s \n Attachment name: %s \n Owner: %s \n Size: %s \n Creator: %s \n Date Created: %s \n Document Summary: %s \n \n Thanks,\n Project Manager\n''' \
                       %(document.title, document.datas_fname, document.name, \
                         document.user_id.name, size, document.create_uid.name, document.create_date, document.description or '')
            self.pool.get('project.project')._log_event(cr, uid, document.res_id, {
                                'res_id' : document.id,
                                'name' : document.name,
                                'description' :desc,#document description,
                                'user_id': uid,
                                'attach' : [(document.datas_fname, document.datas)],
                                'action' : 'create',
                                'type' : 'document'})
        return res

document_file()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

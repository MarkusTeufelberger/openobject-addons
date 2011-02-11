# -*- encoding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2010   Sébastien Beau                                   #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields,osv
import os
import netsvc
import time
import datetime
import base64
from terminator_install import installer
import tools
from tools import config

class kettle_server(osv.osv):
    _name = 'kettle.server'
    _description = 'kettle server'
    
    def button_install(self, cr, uid, ids, context=None):
        inst = installer()
        inst.install(self.read(cr, uid, ids, ['kettle_dir'])[0]['kettle_dir'].replace('data-integration', ''))
        return True
    
    def button_update_terminatooor(self, cr, uid, ids, context=None):
        inst = installer()
        inst.update_terminatoor(self.read(cr, uid, ids, ['kettle_dir'])[0]['kettle_dir'].replace('data-integration', ''))
        return True

    _columns = {
        'name': fields.char('Server Name', size=64, required=True),
        'kettle_dir': fields.char('Kettle Directory', size=255, required=True),
        'transformation': fields.one2many('kettle.transformation', 'server_id', 'Transformation'),
        }
    
    _defaults = {
        'kettle_dir': lambda *a: tools.config['addons_path'].replace('/addons', '/data-integration'),
        }
    
kettle_server()

class kettle_transformation(osv.osv):
    _name = 'kettle.transformation'
    _description = 'kettle transformation'
    
    _columns = {
        'name': fields.char('Transformation Name', size=64, required=True),
        'server_id': fields.many2one('kettle.server', 'Server', required=True),
        'file': fields.binary('File'),
        'filename': fields.char('File Name', size=64),
        }
    
    def error_wizard(self, cr, uid, id, context):
        logger = netsvc.Logger()
        error_description = self.pool.get('ir.attachment').read(cr, uid, id, ['description'], context)['description']
        if error_description:
            if "___USER_ERROR___: " in error_description:
                message = error_description.split("___USER_ERROR___: ")[1].split("\n")[0]
                logger.notifyChannel('kettle-connector', netsvc.LOG_ERROR, "User Error " + message)
                raise osv.except_osv('USER_ERROR', message)
            if "___NO_DATA_FOUND___: " in error_description:
                message = error_description.split("___NO_DATA_FOUND___: ")[1].split("\n")[0]
                logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "empty stream " + message)
                return 'empty_stream'
        logger.notifyChannel('kettle-connector', netsvc.LOG_ERROR, 'An error occurred, please look in the kettle log')
        raise osv.except_osv('KETTLE ERROR', 'An error occurred, please look in the kettle log')
    
    def execute_transformation(self, cr, uid, id, attachment_id, context):
        log_file_name = cr.dbname + '_' + str(config['port']) + '_'+ str(context['default_res_id']) + '_' + str(id) + '_DATE_' + context['start_date'].replace(' ', '_') + ".log"
        transfo = self.browse(cr, uid, id, context)
        kettle_dir = transfo.server_id.kettle_dir
        filename = cr.dbname + '_' + str(config['port']) + '_' + str(context['default_res_id']) + '_' + str(id) + '_' + '_DATE_' + context['start_date'].replace(' ', '_') + transfo.filename
        logger = netsvc.Logger()
        transformation_temp = open(kettle_dir + '/openerp_tmp/'+ filename, 'w')
        
        file_temp = base64.decodestring(transfo.file)
        if context.get('filter', False):
            for key in context['filter']:
                file_temp = file_temp.replace(key, context['filter'][key])
        transformation_temp.write(file_temp)
        transformation_temp.close()
        
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "start kettle task : open kettle log with tail -f " + kettle_dir +'/openerp_tmp/' + log_file_name)
        cmd = "cd " + kettle_dir + "; nohup sh pan.sh -file=openerp_tmp/" + filename + " > openerp_tmp/" + log_file_name
        os_result = os.system(cmd)
        note = self.pool.get('ir.attachment').read(cr, uid, attachment_id, ['description'], context)['description']
        if os_result != 0:
            if note and "___NO_DATA_FOUND___: " in note:
                prefixe_log_name = "[SUCCESS] no data found "
            else:
                prefixe_log_name = "[ERROR]"
        else:
            if note and 'WARNING' in note:
                prefixe_log_name = "[WARNING]"
            else:
                prefixe_log_name = "[SUCCESS]"
        self.pool.get('ir.attachment').write(cr, uid, [attachment_id], {'datas': base64.encodestring(open(kettle_dir +"/openerp_tmp/" + log_file_name, 'rb').read()), 'datas_fname': 'Task.log', 'name' : prefixe_log_name + 'TASK_LOG_'+context['start_date'].replace(' ', '_')}, context)
        cr.commit()
        os.remove(kettle_dir +"/openerp_tmp/" + log_file_name)
        os.remove(kettle_dir + '/openerp_tmp/'+ filename)
        if os_result != 0:
            return self.error_wizard(cr, uid, attachment_id, context)
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "kettle task finish with success")
     
kettle_transformation()

class kettle_task(osv.osv):
    _name = 'kettle.task'
    _description = 'kettle task'    
    
    _columns = {
        'name': fields.char('Task Name', size=64, required=True),
        'server_id': fields.many2one('kettle.server', 'Server', required=True),
        'transformation_id': fields.many2one('kettle.transformation', 'Transformation', required=True),
        'scheduler': fields.many2one('ir.cron', 'Scheduler', readonly=True),
        'parameters': fields.text('Parameters'),
        'upload_file': fields.boolean('Upload File'),
        'output_file' : fields.boolean('Output File'),
        'active_python_code' : fields.boolean('Active Python Code'),
        'python_code_before' : fields.text('Python Code Executed Before Transformation'),
        'python_code_after' : fields.text('Python Code Executed After Transformation'),
        'last_date' : fields.datetime('Last Execution'),
    }
        
    def attach_file_to_task(self, cr, uid, id, file_path, attach_name, delete = False, context = None):
        obj_att = self.pool.get('ir.attachment')
        if not context:
            context = {}
        context.update({'default_res_id' : id, 'default_res_model': 'kettle.task'})
        datas = base64.encodestring(open(file_path,'rb').read())
        os.remove(file_path)
        #For a strange reason I can not apply directly the method create without error if the file_path have an extension
        attachment_id = obj_att.create(cr, uid, {'name': attach_name, 'datas': datas}, context)
        obj_att.write(cr, uid, [attachment_id], {'datas_fname': context.get('force_attach_name', file_path.split("/").pop())}, context)
        return attachment_id
    
    def attach_output_file_to_task(self, cr, uid, id, file_path, attach_name, delete = False, context = None):
        filename_completed = False
        filename = file_path.split('/').pop()
        dir = file_path[0:-len(filename)]
        files = os.listdir(dir)
        for file in files:
            if filename in file:
                filename_completed = file
        if filename_completed:
            note = self.pool.get('ir.attachment').read(cr, uid, context['attachment_id'], ['description'], context)['description']
            if '___OUTPUT_FILE_NAME__: ' in note:
                context['force_attach_name'] = note.split('___OUTPUT_FILE_NAME__: ')[1].split("\n")[0]
            self.attach_file_to_task(cr, uid, id, dir+filename_completed, attach_name, delete, context)
        else:
            raise osv.except_osv('USER ERROR', 'the output file was not found, are you sure that you transformation will give you an output file?')
        
    def execute_python_code(self, cr, uid, id, position, context):
        logger = netsvc.Logger()
        task = self.read(cr, uid, id, ['active_python_code', 'python_code_' + position], context)
        if task['active_python_code'] and task['python_code_' + position]:
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "execute python code " + position +" kettle task")
            exec(task['python_code_' + position])
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "python code executed")
        return context
    
    def start_kettle_task(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        logger = netsvc.Logger()
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        for id in ids:
            context.update({'default_res_id' : id, 'default_res_model': 'kettle.task', 'start_date' : time.strftime('%Y-%m-%d %H:%M:%S')})
            attachment_id = self.pool.get('ir.attachment').create(cr, uid, {'name': 'TASK_LOG_IN_PROGRESS'+context['start_date']}, context)
            cr.commit()
            
            #set parameter
            context['filter'] = {
                      'AUTO_REP_db_erp': str(cr.dbname),
                      'AUTO_REP_user_erp': str(user.login),
                      'AUTO_REP_db_pass_erp': str(user.password),
                      'AUTO_REP_kettle_task_id' : str(id),
                      'AUTO_REP_kettle_task_attachment_id' : str(attachment_id),
                      'AUTO_REP_erp_url' : "http://localhost:" + str(config['port']) + "/xmlrpc"
                      }
            task = self.read(cr, uid, id, ['upload_file', 'parameters', 'transformation_id', 'output_file', 'name', 'server_id', 'last_date'], context)
            context['kettle_dir'] = self.pool.get('kettle.server').read(cr, uid, task['server_id'][0], ['kettle_dir'], context)['kettle_dir']
            
            if task['last_date']:
                context['filter']['AUTO_REP_last_date'] = task['last_date']
                
            if task['output_file']:
                context['filter'].update({'AUTO_REP_file_out' : str('openerp_tmp/output_'+ task['name'] + context['start_date'])})
            
            if task['upload_file']: 
                if not (context and context.get('input_filename',False)):
                    logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "the task " + task['name'] + " can't be executed because the anyone File was uploaded")
                    continue
                else:
                    context['filter'].update({'AUTO_REP_file_in' : str(context['input_filename'])})
            
            #execute python code
            context = self.execute_python_code(cr, uid, id, 'before', context)
            if context.get('stop', False):
                if context['stop'] == 'raise':
                    raise osv.except_osv('Error !', context.get('stop_message', 'An error occure during the execution of the python code'))
                if context['stop'] == 'ok':
                    self.pool.get('ir.attachment').unlink(cr, uid, [attachment_id])
                    return True

            #launch the kettle transformation
            context['filter'].update(eval('{' + str(task['parameters'] or '')+ '}'))
            res = self.pool.get('kettle.transformation').execute_transformation(cr, uid, task['transformation_id'][0], attachment_id, context)

            #execute python code
            context = self.execute_python_code(cr, uid, id, 'after', context)
            if context.get('stop', False):
                if context['stop'] == 'raise':
                    raise osv.except_osv('Error !', context.get('stop_message', 'An error occure during the execution of the python code'))
                if context['stop'] == 'ok':
                    return True
            
            #attach file
            if context.get('input_filename',False):
                self.attach_file_to_task(cr, uid, id, context['input_filename'], '[FILE IN] FILE IMPORTED ' + context['start_date'], True, context)
        
            if task['output_file'] and not res =='empty_stream':
                context['attachment_id'] = attachment_id
                self.attach_output_file_to_task(cr, uid, id, context['filter']['AUTO_REP_file_out'], '[FILE OUT] FILE IMPORTED ' + context['start_date'], True, context)            
            
            self.write(cr, uid, [id], {'last_date' : context['start_date']})
        return True
kettle_task()

class kettle_wizard(osv.osv_memory):
    _name = 'kettle.wizard'
    _description = 'kettle wizard'     

    _columns = {
        'upload_file': fields.boolean("Upload File?"),
        'file': fields.binary('File'),
        'filename': fields.char('Filename', size=64),
    }

    def _get_add_file(self, cr, uid, context):
        return self.pool.get('kettle.task').read(cr, uid, context['active_id'], ['upload_file'])['upload_file']

    _defaults = {
        'upload_file': _get_add_file,
    }

    def _save_file(self, cr, uid, id, vals, context):
        kettle_dir = self.pool.get('kettle.task').browse(cr, uid, context['active_id'], ['server_id'], context).server_id.kettle_dir
        filename = kettle_dir + '/openerp_tmp/' + vals['filename']
        fp = open(filename,'wb+')
        fp.write(base64.decodestring(vals['file']))
        fp.close()
        return filename

    def action_start_task(self, cr, uid, id, context):
        wizard = self.read(cr, uid, id,context=context)[0]
        if wizard['upload_file']:
            if not wizard['file']:
                raise osv.except_osv('Error !', 'You have to select a file before starting the task')
            else:
                context['input_filename'] = self._save_file(cr, uid, id, wizard, context)
        self.pool.get('kettle.task').start_kettle_task(cr, uid, [context['active_id']], context)
        return {'type': 'ir.actions.act_window_close'}

kettle_wizard()

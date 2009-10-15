# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from gdata import service
import gdata
import atom

import wizard
import pooler
from osv import osv,fields

_blog_form =  '''<?xml version="1.0"?>
        <form string="Export">
        <separator string="Export Tasks to Blog" colspan="4"/>
            <field name="blog_id" domain = "[('user_id','=', uid)]" height="300" width="700" nolabel="1" required="True"/>
        </form> '''

_blog_fields = {
        'blog_id': {'string': 'Export ', 'type': 'many2many', 'relation':'project.task'},
        }

_summary_form = '''<?xml version="1.0"?>
        <form string="Summary">
            <field name="summary" nolabel="1" height="20" width="200" />
        </form> '''

_summary_fields = {
            'summary': {'string': 'Summary', 'type': 'text', 'required': False, 'readonly': True},
        }

class google_blogger_wizard(wizard.interface):

    blog_service = ""
    blog_id = ""
    def _export_task(self, cr, uid, data, context):
        obj_user = pooler.get_pool(cr.dbname).get('res.users')
        blog_auth_details = obj_user.read(cr, uid, uid, [])
        if not blog_auth_details['blogger_email'] or not blog_auth_details['blogger_password']:
            raise osv.except_osv('Warning !',
                                 'Please  blogger Enter email id and password in users')
        try:
            self.blog_service = service.GDataService(blog_auth_details['blogger_email'], blog_auth_details['blogger_password'])
            self.blog_service.source = 'Tiny'
            self.blog_service.service = 'blogger'
            self.blog_service.server = 'www.blogger.com'
            self.blog_service.ProgrammaticLogin()
            feed = self.blog_service.Get('/feeds/default/blogs')
            self_link = feed.entry[0].GetSelfLink()
            if self_link:
                self.blog_id = self_link.href.split('/')[-1]
            obj_task = pooler.get_pool(cr.dbname).get('project.task')
            data_task = obj_task.read(cr, uid, data['form']['blog_id'][0][2], [])
            for task in data_task:
                entry = gdata.GDataEntry()
                entry.author.append(atom.Author(atom.Name(text='uid')))
                entry.title = atom.Title(title_type='xhtml', text=task['name'])
                entry.content = atom.Content(content_type='html', text=task['description'])
                self.blog_service.Post(entry,
                '/feeds/' + self.blog_id + '/posts/default')
            return {'summary':'Succefully sent tasks to blogger'}
        except Exception, e:
            raise osv.except_osv('Error !',e )

    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch':_blog_form, 'fields':_blog_fields,  'state':[('end','Cancel'),('export','Export to Blog')]}
        },
        'export': {
            'actions': [_export_task],
            'result': {'type': 'form', 'arch': _summary_form, 'fields': _summary_fields, 'state': [('end', 'Ok')]}
        }
    }

google_blogger_wizard('google.blogger')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
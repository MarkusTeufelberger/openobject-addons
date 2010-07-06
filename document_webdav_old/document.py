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
from webdav.content_index import content_index
import base64

from osv import osv, fields
import urlparse

import webdav
import webdav.DAV.errors
import os

import pooler

# Unsupported WebDAV Commands:
#     label
#     search
#     checkin
#     checkout
#     propget
#     propset

#
# An object that represent an uri
#   path: the uri of the object
#   content: the Content it belongs to (_print.pdf)
#   type: content or collection
#       content: objct = res.partner
#       collection: object = directory, object2 = res.partner
#       file: objct = ir.attachement
#   root: if we are at the first directory of a ressource
#
INVALID_CHARS={'*':str(hash('*')), '|':str(hash('|')) , "\\":str(hash("\\")), '/':'__', ':':str(hash(':')), '"':str(hash('"')), '<':str(hash('<')) , '>':str(hash('>')) , '?':str(hash('?'))}
class node_class(object):
	def __init__(self, cr, uid, path,object,object2=False, context={}, content=False, type='collection', root=False):
		self.cr = cr
		self.uid = uid
		self.path = path
		self.object = object
		self.object2 = object2
		self.context = context
		self.content = content
		self.type=type
		self.root=root

	def _file_get(self, nodename=False):
		if not self.object:
			return []
		pool = pooler.get_pool(self.cr.dbname)
		fobj = pool.get('ir.attachment')
		res2 = []
		where = []
		if self.object2:
			where.append( ('res_model','=',self.object2._name) )
			where.append( ('res_id','=',self.object2.id) )
			for content in self.object.content_ids:
				test_nodename = self.object2.name + (content.suffix or '') + (content.extension or '')
				if test_nodename.find('/'):
					test_nodename=test_nodename.replace('/', '_')
				path = self.path+'/'+test_nodename
				#path = self.path+'/'+self.object2.name + (content.suffix or '') + (content.extension or '')
				if not nodename:
					n = node_class(self.cr, self.uid,path, self.object2, False, content=content, type='content')
					res2.append( n)
				else:
					if nodename == test_nodename:
						n = node_class(self.cr, self.uid, path, self.object2, False, content=content, type='content')
						res2.append(n)
		else:
			where.append( ('parent_id','=',self.object.id) )
			where.append( ('res_id','=',False) )
		if nodename:
			where.append( (fobj._rec_name,'=',nodename) )
		ids = fobj.search(self.cr, self.uid, where+[ ('parent_id','=',self.object and self.object.id or False) ], context=self.context)
		if self.object and self.root:
			ids += fobj.search(self.cr, self.uid, where+[ ('parent_id','=',False) ], context=self.context)
		res = fobj.browse(self.cr, self.uid, ids, context=self.context)
		return map(lambda x: node_class(self.cr, self.uid, self.path+'/'+x.name, x, False, type='file'), res) + res2


	def directory_list_for_child(self,nodename,parent=False):
		pool = pooler.get_pool(self.cr.dbname)
		where = []
		if nodename:
			where.append(('name','=',nodename))
		where.append(('parent_id','=',self.object and self.object.id or False))
		ids = pool.get('document.directory').search(self.cr, self.uid, where+[('ressource_id','=',0)], self.context)
		if self.object2:
			ids += pool.get('document.directory').search(self.cr, self.uid, where+[('ressource_id','=',self.object2.id)], self.context)
		res = pool.get('document.directory').browse(self.cr, self.uid, ids,self.context)
		return res

	def _child_get(self, nodename=False):
		if self.type not in ('collection','database'):
			return []
		res = self.directory_list_for_child(nodename)
		result= map(lambda x: node_class(self.cr, self.uid, self.path+'/'+x.name, x, self.object2), res)
		if self.type=='database':
			pool = pooler.get_pool(self.cr.dbname)
			fobj = pool.get('ir.attachment')
			file_ids=fobj.search(self.cr,self.uid,[('parent_id','=',False)])
			res = fobj.browse(self.cr, self.uid, file_ids, context=self.context)
			result +=map(lambda x: node_class(self.cr, self.uid, self.path+'/'+x.name, x, False, type='file'), res)
		if self.type=='collection' and self.object.type=="ressource":
			where = self.object.domain and eval(self.object.domain) or []
			obj = self.object2

			if not self.object2:
				pool = pooler.get_pool(self.cr.dbname)
				obj = pool.get(self.object.ressource_type_id.model)

			if self.object.ressource_tree:
				if obj._parent_name in obj.fields_get(self.cr,self.uid):
					where.append((obj._parent_name,'=',self.object2 and self.object2.id or False))
				else :
					if self.object2:
						return result
			else:
				if self.object2:
					return result

			name_for = obj._name.split('.')[-1]
			if nodename  and nodename.find(name_for) == 0  :
				id = int(nodename.replace(name_for,''))
				where.append(('id','=',id))
			elif nodename:
				if nodename.find('__') :
					nodename=nodename.replace('__','/')
				for invalid in INVALID_CHARS:
					if nodename.find(INVALID_CHARS[invalid]) :
						nodename=nodename.replace(INVALID_CHARS[invalid],invalid)
				where.append(('name','=',nodename))
			ids = obj.search(self.cr, self.uid, where, self.context)
			res = obj.browse(self.cr, self.uid, ids,self.context)
			for r in res:
				if not r.name:
					r.name = name_for+'%d'%r.id
				for invalid in INVALID_CHARS:
					if r.name.find(invalid) :
						r.name=r.name.replace(invalid,INVALID_CHARS[invalid])
			result2 = map(lambda x: node_class(self.cr, self.uid, self.path+'/'+x.name.replace('/','__'), self.object, x, root=True), res)
			if result2:
				result = result2
		return result

	def children(self):
		return self._child_get() + self._file_get()

	def child(self, name):
		res = self._child_get(name)
		if res:
			return res[0]
		res = self._file_get(name)
		if res:
			return res[0]
		raise webdav.DAV.errors.DAV_NotFound

	def path_get(self):
		path = self.path
		if self.path[0]=='/':
			path = self.path[1:]
		return path

class document_directory(osv.osv):
	_name = 'document.directory'
	_description = 'Document directory'
	_columns = {
		'name': fields.char('Name', size=64, required=True, select=1),
		'write_date': fields.datetime('Date Modified', readonly=True),
		'write_uid':  fields.many2one('res.users', 'Last Modification User', readonly=True),
		'create_date': fields.datetime('Date Created', readonly=True),
		'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
		'file_type': fields.char('Content Type', size=32),
		'domain': fields.char('Domain', size=128),
		'user_id': fields.many2one('res.users', 'Owner'),
		'group_ids': fields.many2many('res.groups', 'document_directory_group_rel', 'item_id', 'group_id', 'Groups'),
		'parent_id': fields.many2one('document.directory', 'Parent Item'),
		'child_ids': fields.one2many('document.directory', 'parent_id', 'Children'),
		'file_ids': fields.one2many('ir.attachment', 'parent_id', 'Files'),
		'content_ids': fields.one2many('document.directory.content', 'directory_id', 'Virtual Files'),
		'type': fields.selection([('directory','Static Directory'),('ressource','Other Ressources')], 'Type', required=True),
		'ressource_type_id': fields.many2one('ir.model', 'Ressource Model'),
		'ressource_id': fields.integer('Ressource ID'),
		'ressource_tree': fields.boolean('Tree Structure'),
	}
	_defaults = {
		'user_id': lambda self,cr,uid,ctx: uid,
		'domain': lambda self,cr,uid,ctx: '[]',
		'type': lambda *args: 'directory',
	}
	_sql_constraints = [
		('filename_uniq', 'unique (name,parent_id,ressource_id)', 'The directory name must be unique !')
	]
	def _check_recursion(self, cr, uid, ids):
		level = 100
		while len(ids):
			cr.execute('select distinct parent_id from document_directory where id in ('+','.join(map(str,ids))+')')
			ids = filter(None, map(lambda x:x[0], cr.fetchall()))
			if not level:
				return False
			level -= 1
		return True

	_constraints = [
		(_check_recursion, 'Error! You can not create recursive Directories.', ['parent_id'])
	]
	def __init__(self, *args, **kwargs):
		res = super(document_directory, self).__init__(*args, **kwargs)
		self._cache = {}
		return res

	def onchange_content_id(self, cr, uid, ids, ressource_type_id):
		return {}

	def _get_childs(self, cr, uid, node, nodename=False, context={}):
		where = []
		if nodename:
			where.append(('name','=',nodename))
		if object:
			where.append(('parent_id','=',object.id))
		ids = self.search(cr, uid, where, context)
		return self.browse(cr, uid, ids, context), False

	"""
		PRE:
			uri: of the form "Sales Order/SO001"
		PORT:
			uri
			object: the object.directory or object.directory.content
			object2: the other object linked (if object.directory.content)
	"""
	def get_object(self, cr, uid, uri, context={}):
		if not uri:
			return None
		turi = tuple(uri)
		if (turi in self._cache):
			(path, oo, oo2, content,type,root) = self._cache[turi]
			if oo:
				object = self.pool.get(oo[0]).browse(cr, uid, oo[1], context)
			else:
				object = False
			if oo2:
				object2 = self.pool.get(oo2[0]).browse(cr, uid, oo2[1], context)
			else:
				object2 = False
			node = node_class(cr, uid, path, object,object2, context, content, type, root)
			return node

		node = node_class(cr, uid, uri[0], False, type='database')
		for path in uri[1:]:
			if path:
				node = node.child(path)
		oo = node.object and (node.object._name, node.object.id) or False
		oo2 = node.object2 and (node.object2._name, node.object2.id) or False
		self._cache[turi] = (node.path, oo, oo2, node.content,node.type,node.root)
		return node

	def get_childs(self, cr, uid, uri, context={}):
		node = self.get_object(cr, uid, uri, context)
		if uri:
			children = node.children()
		else:
			children= [node]
		result = map(lambda node: node.path_get(), children)
		#childs,object2 = self._get_childs(cr, uid, object, False, context)
		#result = map(lambda x: urlparse.urljoin(path+'/',x.name), childs)
		return result

	def create(self, cr, uid, vals, context=None):
		if vals.get('name',False) and (vals.get('name').find('/')+1 or vals.get('name').find('@')+1 or vals.get('name').find('$')+1 or vals.get('name').find('#')+1) :
			raise webdav.DAV.errors.DAV_NotFound('Directory name must not contain special character...')
		return super(document_directory,self).create(cr, uid, vals, context)

document_directory()

class document_directory_content(osv.osv):
	_name = 'document.directory.content'
	_description = 'Directory Content'
	_order = "sequence"
	_columns = {
		'name': fields.char('Content Name', size=64, required=True),
		'sequence': fields.integer('Sequence', size=16),
		'suffix': fields.char('Suffix', size=16),
		'versioning': fields.boolean('Versioning'),
		'report_id': fields.many2one('ir.actions.report.xml', 'Report', required=True),
		'extension': fields.selection([('.pdf','.pdf'),('','None')], 'Extension', required=True),
		'directory_id': fields.many2one('document.directory', 'Directory')
	}
	_defaults = {
		'extension': lambda *args: '',
		'sequence': lambda *args: 1
	}
document_directory_content()

class ir_action_report_xml(osv.osv):
	_name="ir.actions.report.xml"
	_inherit ="ir.actions.report.xml"

	def _model_get(self, cr, uid, ids, name, arg, context):
		res = {}
		model_pool = self.pool.get('ir.model')
		for data in self.read(cr,uid,ids,['model']):
			model = data.get('model',False)
			if model:
				model_id =model_pool.search(cr,uid,[('model','=',model)])
				if model_id:
					res[data.get('id')] = model_id[0]
				else:
					res[data.get('id')] = False
		return res

	def _model_search(self, cr, uid, obj, name, args, context={}):
		if not len(args):
			return []
		model_id= args[0][2]
		if not model_id:
			return []
		model = self.pool.get('ir.model').read(cr,uid,[model_id])[0]['model']
		report_id = self.search(cr,uid,[('model','=',model)])
		if not report_id:
			return [('id','=','0')]
		return [('id','in',report_id)]

	_columns={
		'model_id' : fields.function(_model_get,fnct_search=_model_search,method=True,string='Model Id'),
	}

ir_action_report_xml()


import random
import string


def random_name():
	random.seed()
	d = [random.choice(string.letters) for x in xrange(10) ]
	name = "".join(d)
	return name


def create_directory(path):
	dir_name = random_name()
	path = os.path.join(path,dir_name)
	os.mkdir(path)
	return dir_name

class document_file(osv.osv):
	_inherit = 'ir.attachment'
	def _data_get(self, cr, uid, ids, name, arg, context):
		result = {}
		cr.execute('select id,store_method,datas,store_fname,link from ir_attachment where id in ('+','.join(map(str,ids))+')')
		for id,m,d,r,l in cr.fetchall():
			if m=='db':
				result[id] = d
			elif m=='fs':
				path = os.path.join(os.getcwd(),'filestore')
				value = file(os.path.join(path,r), 'rb').read()
				result[id] = base64.encodestring(value)
			else:
				result[id] = ''
		return result

	#
	# This code can be improved
	#
	def _data_set(self, cr, obj, id, name, value, uid=None, context={}):
		if not value:
			return True
		if (not context) or context.get('store_method','fs')=='fs':
			path = os.path.join(os.getcwd(), "filestore")
			if not os.path.isdir(path):
				os.mkdir(path)
			flag = None
			for dirs in os.listdir(path):
				if os.path.isdir(os.path.join(path,dirs)) and len(os.listdir(os.path.join(path,dirs)))<4000:
					flag = dirs
					break
			flag = flag or create_directory(path)
			filename = random_name()
			fname = os.path.join(path, flag, filename)
			fp = file(fname,'wb')
			fp.write(base64.decodestring(value))
			filesize = os.stat(fname).st_size
			cr.execute('update ir_attachment set store_fname=%s,store_method=%s,file_size=%d where id=%d', (os.path.join(flag,filename),'fs',filesize,id))
		else:
			cr.execute('update ir_attachment set datas=%s,store_method=%s where id=%d', (psycopg.Binary(value),'db',id))
		return True

	_columns = {
		'user_id': fields.many2one('res.users', 'Owner', select=1),
		'group_ids': fields.many2many('res.groups', 'document_directory_group_rel', 'item_id', 'group_id', 'Groups'),
		'parent_id': fields.many2one('document.directory', 'Directory', select=1),
		'file_size': fields.integer('File Size', required=True),
		'file_type': fields.char('Content Type', size=32),
		'index_content': fields.text('Indexed Content'),
		'write_date': fields.datetime('Date Modified', readonly=True),
		'write_uid':  fields.many2one('res.users', 'Last Modification User', readonly=True),
		'create_date': fields.datetime('Date Created', readonly=True),
		'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
		'store_method': fields.selection([('db','Database'),('fs','Filesystem'),('link','Link')], "Storing Method"),
		'datas': fields.function(_data_get,method=True,store=True,fnct_inv=_data_set,string='File Content',type="binary"),
		'store_fname': fields.char('Stored Filename', size=200),
		'res_model': fields.char('Attached Model', size=64), #res_model
		'res_id': fields.integer('Attached ID'), #res_id
		'partner_id':fields.many2one('res.partner', 'Partner', select=1),
		'title': fields.char('Resource Title',size=64),
	}

	_defaults = {
		'user_id': lambda self,cr,uid,ctx:uid,
		'file_size': lambda self,cr,uid,ctx:0,
		'store_method': lambda *args: 'db'
	}
	def write(self, cr, uid, ids, vals, context=None):
		result = super(document_file,self).write(cr,uid,ids,vals,context=context)
		try:
			for f in self.browse(cr, uid, ids, context=context):
				if 'datas' not in vals:
					vals['datas']=f.datas
				res = content_index(base64.decodestring(vals['datas']), f.datas_fname, f.file_type or None)
				super(document_file,self).write(cr, uid, ids, {
					'index_content': res
				})
		except:
			pass
		return result

	def create(self, cr, uid, vals, context={}):
		vals['title']=vals['name']
		if vals.get('res_id', False) and vals.get('res_model',False):
			obj_model=self.pool.get(vals['res_model'])
			result = obj_model.browse(cr, uid, [vals['res_id']], context=context)
			if len(result):
				vals['title'] = (result[0].name or '')[:60]
				if obj_model._name=='res.partner':
					vals['partner_id']=result[0].id
				elif 'address_id' in result[0]:
					vals['partner_id']=result[0].address_id.partner_id.id or False
				else:
					vals['partner_id']='partner_id' in result[0] and result[0].partner_id.id or False

			if 'parent_id' not in vals:
				obj_directory=self.pool.get('document.directory')
				directory_ids=obj_directory.search(cr,uid,[('ressource_type_id','=',vals['res_model'])])
				dirs=obj_directory.browse(cr,uid,directory_ids)
				for dir in dirs:
					if dir.domain:
						object_ids=obj_model.search(cr,uid,eval(dir.domain))
						if vals['res_id'] in object_ids:
							vals['parent_id']=dir.id
		datas=None
		if 'datas' not in vals:
			import urllib
			datas=base64.encodestring(urllib.urlopen(vals['link']).read())
		else:
			datas=vals['datas']
		vals['file_size']= len(datas)
		result = super(document_file,self).create(cr, uid, vals, context)
		cr.commit()
		try:
			res = content_index(base64.decodestring(datas), vals['datas_fname'], vals.get('content_type', None))
			super(document_file,self).write(cr, uid, [result], {
				'index_content': res,
			})
		except:
			pass
		return result

	def unlink(self,cr, uid, ids, context={}):
		for f in self.browse(cr, uid, ids, context):
			if f.store_method=='fs':
				path = os.path.join(os.getcwd(),'filestore',f.store_fname)
				os.unlink(path)
		return super(document_file, self).unlink(cr, uid, ids, context)
document_file()

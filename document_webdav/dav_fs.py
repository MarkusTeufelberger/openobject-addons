# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import pooler

import base64
import sys
import os
import time
from string import joinfields, split, lower

from DAV import AuthServer
from service import security
import dav_auth

import netsvc
import urlparse

from DAV.constants import COLLECTION, OBJECT
from DAV.errors import *
from DAV.iface import *
import urllib

from DAV.davcmd import copyone, copytree, moveone, movetree, delone, deltree

from cache import memoize

CACHE_SIZE=20000

#hack for urlparse: add webdav in the net protocols
urlparse.uses_netloc.append('webdav')

def _to_unicode(s):
    try:
        return s.decode('utf-8')
    except UnicodeError:
        try:
            return s.decode('latin')
        except UnicodeError:
            try:
                return s.encode('ascii')
            except UnicodeError:
                return s

def _to_decode(s):
    try:
        return s.encode('utf-8')
    except UnicodeError:
        try:
            return s.encode('latin')
        except UnicodeError:
            try:
                return s.decode('ascii')
            except UnicodeError:
                return s  

class tinyerp_handler(dav_interface):
    """
    This class models a Tiny ERP interface for the DAV server
    """
    def __init__(self,  host,port,  verbose=False):
        self.db_name = False
        self.directory_id=False
        self.host=host
        self.port=port
        self.baseuri = 'http://%s:%s/' % (self.host, self.port)
        self.db_name_list=[]
#
#
#    def get_db(self,uri):
#        names=self.uri2local(uri).split('/')
#        self.db_name=False
#        if len(names) > 1:
#            self.db_name=self.uri2local(uri).split('/')[1]
#            if self.db_name=='':
#                raise Exception,'Plese specify Database name in folder'
#        return self.db_name
#


    @memoize(4)
    def db_list(self):
        s = netsvc.LocalService('db')
        result = s.list()
        self.db_name_list=[]
        for db_name in result:
            db = pooler.get_db_only(db_name)
            cr = db.cursor()
            cr.execute("select id from ir_module_module where name = 'document' and state='installed' ")
            res=cr.fetchone()
            if res and len(res):
                self.db_name_list.append(db_name)
            cr.close()
        return self.db_name_list

    def get_childs(self,uri):
        """ return the child objects as self.baseuris for the given URI """
        if uri[-1]=='/':uri=uri[:-1]
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        
        if not dbname:
            s = netsvc.LocalService('db')
            return map(lambda x: urlparse.urljoin(self.baseuri, x), self.db_list())
        result = []
        node = self.uri2object(cr,uid,pool, uri2[:])
        if not node:
            raise DAV_NotFound(uri2)
        elif node.type in ('collection','database'):
            for d in node.children():
                result.append( urlparse.urljoin(self.baseuri,dbname+'/' + d.path) )
        return result

    def uri2local(self, uri):
        uparts=urlparse.urlparse(uri)
        reluri=uparts[2]
        if reluri and reluri[-1]=="/":
            reluri=reluri[:-1]
        return reluri

    #
    # pos: -1 to get the parent of the uri
    #
    def get_cr(self, uri):
        reluri = self.uri2local(uri)
        try:
            dbname = reluri.split('/')[1]
        except:
            dbname = False
        if not dbname:
            return None, None, None, False, None
        if dav_auth.auth['user'] == 'root':
            uid = 1
        else:
            uid = security.login(dbname, dav_auth.auth['user'], dav_auth.auth['pwd'])
        db,pool = pooler.get_db_and_pool(dbname)
        cr = db.cursor()
        uri2 = reluri.split('/')[2:]
        return cr, uid, pool, dbname, uri2

    def uri2object(self, cr,uid, pool,uri):
        if not uid:
            return None
        return pool.get('document.directory').get_object(cr, uid, uri)

    def get_data(self,uri):
        if uri[-1]=='/':uri=uri[:-1]
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            raise DAV_Error, 409
        node = self.uri2object(cr,uid,pool, uri2)
        if not node:
            raise DAV_NotFound(uri2)
        if node.type == 'file':
            datas = False
            if node.object.datas:
                datas=node.object.datas
            elif node.object.link:
                import urllib
                datas=base64.encodestring(urllib.urlopen(node.object.link).read())
            res = base64.decodestring(datas or '')
            res = _to_unicode(res).encode('ascii','replace')
            return res
        elif node.type=='content':
            cr = node.cr
            uid = node.uid
            pool = pooler.get_pool(cr.dbname)
            pdf = getattr(pool.get('document.directory.content'), 'process_read_'+node.content.extension[1:])(cr, uid, node)
            datas=base64.encodestring(pdf.read())            
            res =  base64.decodestring(datas or '')  
            res = _to_unicode(res).encode('ascii','replace')
            return res
        else:
            raise DAV_Forbidden

    @memoize(CACHE_SIZE)
    def _get_dav_resourcetype(self,uri):
        """ return type of object """
        self.parent.log(netsvc.LOG_INFO, 'RT : %s'%uri)
        if uri[-1]=='/':uri=uri[:-1]
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            return COLLECTION
        node = self.uri2object(cr,uid,pool, uri2)
        if not node:
            raise DAV_NotFound(uri2)
        cr.close()
        if node.type in ('collection','database'):
            return COLLECTION
        return OBJECT

    def _get_dav_displayname(self,uri):
        # TODO!
        raise DAV_Secret

    @memoize(CACHE_SIZE)
    def _get_dav_getcontentlength(self,uri):
        """ return the content length of an object """
        if uri[-1]=='/':uri=uri[:-1]
        result = 0
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            return '0'
        node = self.uri2object(cr, uid, pool, uri2)
        if not node:
            raise DAV_NotFound(uri2)
        if node.type=='file':
            result = node.object.file_size or 0
        cr.close()
        return str(result)

    @memoize(CACHE_SIZE)
    def get_lastmodified(self,uri):
        """ return the last modified date of the object """
        self.parent.log(netsvc.LOG_INFO,'Get DAV Mod : %s'%uri)
        if uri[-1]=='/':uri=uri[:-1]
        today = time.time()
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            return today
        node = self.uri2object(cr,uid,pool, uri2)
        if not node:
            raise DAV_NotFound(uri2)
        if node.type=='file':
            dt = node.object.write_date or node.object.create_date
            result = time.mktime(time.strptime(dt,'%Y-%m-%d %H:%M:%S'))
        else:
            result = today
        cr.close()
        return result

    @memoize(CACHE_SIZE)
    def get_creationdate(self,uri):
        """ return the last modified date of the object """

        if uri[-1]=='/':uri=uri[:-1]
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            raise DAV_Error, 409
        node = self.uri2object(cr,uid,pool, uri2)
        if not node:
            raise DAV_NotFound(uri2)
        if node.type=='file':
            dt = node.object.write_date or node.object.create_date
            result = time.strptime(dt,'%Y-%m-%d %H:%M:%S')
        else:
            result = time.time()
        cr.close()
        return result

    @memoize(CACHE_SIZE)
    def _get_dav_getcontenttype(self,uri):
        if uri[-1]=='/':uri=uri[:-1]
        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            return 'httpd/unix-directory'
        node = self.uri2object(cr,uid,pool, uri2)
        if not node:
            raise DAV_NotFound(uri2)
            
        result = 'application/octet-stream'
        if node.type in ('collection','database'):
            result ='httpd/unix-directory'
        elif node.type == 'content':            
            result = 'application/%s'%node.content.extension[1:]
        elif node.type == 'file':
            try:
                ftype = node.object.file_type
                if ftype and  '/' in ftype:
                    result = ftype
            except Exception,e:
                self.parent.log(netsvc.LOG_ERROR, e)
                pass
        cr.close()
        return result
        #raise DAV_NotFound, 'Could not find %s' % path

    def mkcol(self,uri):
        """ create a new collection """
        self.parent.log(netsvc.LOG_INFO,'MKCOL : %s'%uri)
        if uri[-1]=='/':uri=uri[:-1]
        parent='/'.join(uri.split('/')[:-1])
        if not parent.startswith(self.baseuri):
            parent=self.baseuri + ''.join(parent[1:])
        if not uri.startswith(self.baseuri):
            uri=self.baseuri + ''.join(uri[1:])


        cr, uid, pool,dbname, uri2 = self.get_cr(uri)
        if not dbname:
            raise DAV_Error, 409
        node = self.uri2object(cr,uid,pool, uri2[:-1])
        object2=node and node.object2 or False
        object=node and node.object or False

        objname = uri2[-1]
        if not object:
            pool.get('document.directory').create(cr, uid, {
                'name': objname,
                'parent_id': False,
                'ressource_type_id': False,
                'ressource_id': False
            })
        else:
            pool.get('document.directory').create(cr, uid, {
                'name': objname,
                'parent_id': object.id,
                'ressource_type_id': object.ressource_type_id.id,
                'ressource_id': object2 and object2.id or False
            })

        cr.commit()
        cr.close()
        return True

    def put(self,uri,data,content_type=None):
        """ put the object into the filesystem """
        self.parent.log(netsvc.LOG_INFO, 'Putting %s (%d), %s'%( unicode(uri,'utf8'), len(data), content_type))
        parent='/'.join(uri.split('/')[:-1])
        cr, uid, pool,dbname, uri2 = self.get_cr(uri)
        if not dbname:
            raise DAV_Forbidden
        try:
            node = self.uri2object(cr,uid,pool, uri2[:])
        except:
            node = False
        fobj = pool.get('ir.attachment')
        objname = uri2[-1]
        ext = objname.find('.') >0 and objname.split('.')[1] or False
        if node and node.type=='file':
            val = {
                'file_size': len(data),
                'datas': base64.encodestring(data),
            }
            cid = fobj.write(cr, uid, [node.object.id], val)
            cr.commit()
        elif not node:
            node = self.uri2object(cr,uid,pool, uri2[:-1])
            object2=node and node.object2 or False
            object=node and node.object or False
            val = {
                'name': objname,
                'datas_fname': objname,
                'file_size': len(data),
                'datas': base64.encodestring(data),
                'parent_id': object and object.id or False,
            }
            partner = False
            if object2:
                if object2.partner_id and object2.partner_id.id:
                    partner = object2.partner_id.id
                if object2._name == 'res.partner':
                    partner = object2.id
                val.update( {
                    'res_model': object2._name,
                    'partner_id': partner,
                    'res_id': object2.id
                })
            cid = fobj.create(cr, uid, val)
            cr.commit()

            # TODO: Test Permissions
            if False:
                raise DAV_Forbidden
            cr.close()
            return 201
        else:
            raise DAV_Forbidden

    def rmcol(self,uri):
        """ delete a collection """
        if uri[-1]=='/':uri=uri[:-1]

        cr, uid, pool, dbname, uri2 = self.get_cr(uri)
        if not dbname:
            raise DAV_Error, 409
        node = self.uri2object(cr,uid,pool, uri2)
        object2=node and node.object2 or False
        object=node and node.object or False
        if object._table_name=='document.directory':
            if object.child_ids:
                raise DAV_Forbidden # forbidden
            if object.file_ids:
                raise DAV_Forbidden # forbidden
            res = pool.get('document.directory').unlink(cr, uid, [object.id])

        cr.commit()
        cr.close()
        return 204

    def rm(self,uri):
        if uri[-1]=='/':uri=uri[:-1]        
        object=False
        cr, uid, pool,dbname, uri2 = self.get_cr(uri)
        if not dbname:
            raise DAV_Error, 409
        node = self.uri2object(cr,uid,pool, uri2)
        object2=node and node.object2 or False
        object=node and node.object or False
        if not object:
            raise DAV_NotFound

        self.parent.log(netsvc.LOG_INFO,' rm : %s,%s'%(object._table_name,uri))
        if object._table_name=='ir.attachment':
            res = pool.get('ir.attachment').unlink(cr, uid, [object.id])
        else:
            raise DAV_Forbidden # forbidden
        parent='/'.join(uri.split('/')[:-1])
        cr.commit()
        cr.close()
        return 204

    ### DELETE handlers (examples)
    ### (we use the predefined methods in davcmd instead of doing
    ### a rm directly
    ###

    def delone(self,uri):
        """ delete a single resource

        You have to return a result dict of the form
        uri:error_code
        or None if everything's ok

        """
        if uri[-1]=='/':uri=uri[:-1]
        res=delone(self,uri)
        parent='/'.join(uri.split('/')[:-1])
        return res

    def deltree(self,uri):
        """ delete a collection

        You have to return a result dict of the form
        uri:error_code
        or None if everything's ok
        """
        if uri[-1]=='/':uri=uri[:-1]
        res=deltree(self,uri)
        parent='/'.join(uri.split('/')[:-1])
        return res


    ###
    ### MOVE handlers (examples)
    ###

    def moveone(self,src,dst,overwrite):
        """ move one resource with Depth=0

        an alternative implementation would be

        result_code=201
        if overwrite:
            result_code=204
            r=os.system("rm -f '%s'" %dst)
            if r: return 412
        r=os.system("mv '%s' '%s'" %(src,dst))
        if r: return 412
        return result_code

        (untested!). This would not use the davcmd functions
        and thus can only detect errors directly on the root node.
        """
        res=moveone(self,src,dst,overwrite)
        return res

    def movetree(self,src,dst,overwrite):
        """ move a collection with Depth=infinity

        an alternative implementation would be

        result_code=201
        if overwrite:
            result_code=204
            r=os.system("rm -rf '%s'" %dst)
            if r: return 412
        r=os.system("mv '%s' '%s'" %(src,dst))
        if r: return 412
        return result_code

        (untested!). This would not use the davcmd functions
        and thus can only detect errors directly on the root node"""

        res=movetree(self,src,dst,overwrite)
        return res

    ###
    ### COPY handlers
    ###

    def copyone(self,src,dst,overwrite):
        """ copy one resource with Depth=0

        an alternative implementation would be

        result_code=201
        if overwrite:
            result_code=204
            r=os.system("rm -f '%s'" %dst)
            if r: return 412
        r=os.system("cp '%s' '%s'" %(src,dst))
        if r: return 412
        return result_code

        (untested!). This would not use the davcmd functions
        and thus can only detect errors directly on the root node.
        """
        res=copyone(self,src,dst,overwrite)
        return res

    def copytree(self,src,dst,overwrite):
        """ copy a collection with Depth=infinity

        an alternative implementation would be

        result_code=201
        if overwrite:
            result_code=204
            r=os.system("rm -rf '%s'" %dst)
            if r: return 412
        r=os.system("cp -r '%s' '%s'" %(src,dst))
        if r: return 412
        return result_code

        (untested!). This would not use the davcmd functions
        and thus can only detect errors directly on the root node"""
        res=copytree(self,src,dst,overwrite)
        return res

    ###
    ### copy methods.
    ### This methods actually copy something. low-level
    ### They are called by the davcmd utility functions
    ### copytree and copyone (not the above!)
    ### Look in davcmd.py for further details.
    ###

    def copy(self,src,dst):
        src=urllib.unquote(src)
        dst=urllib.unquote(dst)
        ct = self._get_dav_getcontenttype(src)
        data = self.get_data(src)
        self.put(dst,data,ct)
        return 201

    def copycol(self,src,dst):
        """ copy a collection.

        As this is not recursive (the davserver recurses itself)
        we will only create a new directory here. For some more
        advanced systems we might also have to copy properties from
        the source to the destination.
        """
        self.parent.log(netsvc.LOG_INFO,"Copy a collection.")
        return self.mkcol(dst)


    def exists(self,uri):
        """ test if a resource exists """
        result = False
        cr, uid, pool,dbname, uri2 = self.get_cr(uri)
        if not dbname:
            return True
        try:
            node = self.uri2object(cr,uid,pool, uri2)
            if node:
                result = True
        except:
            pass
        cr.close()
        return result

    @memoize(CACHE_SIZE)
    def is_collection(self,uri):
        """ test if the given uri is a collection """
        return self._get_dav_resourcetype(uri)==COLLECTION

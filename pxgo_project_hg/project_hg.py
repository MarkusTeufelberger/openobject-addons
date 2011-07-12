# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Santiago Argüeso Armesto$
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

from osv import fields, osv, orm
from mercurial import ui, hg, util
import datetime, time
import re

def find_changes_in_repo(repos, date):

    # returns true if d2 is newer than d1
    def newerDate(d1, d2):
         d1 = datetime.datetime.fromtimestamp(d1)
         d2 = datetime.datetime.fromtimestamp(d2)
         return d1 < d2

    changes = repos.changelog

    out = []

    # filter on date
    if date != '':
        changes = [change for change in changes if newerDate(date, repos.changectx(change).date()[0]) ]

    return changes


class scrum_project(osv.osv):
    _inherit = 'scrum.project'
    _description = 'Scrum Project'
    _columns= {
        'hg_repo_path':fields.char('Hg repository path', size=256)
    }

    def load_changeset (self, cr, uid, ids, *args):

        projects= self.browse(cr,uid,ids)
        for project in projects:

            cr.execute("SELECT max(date) FROM hg_changeset WHERE project_id="+str(project.id))
            max_date=cr.fetchone()[0]
            if max_date:
                date = util.parsedate(max_date)[0]
            else:
                date=''

            repo = hg.repository(ui.ui(), project.hg_repo_path)
            changes = find_changes_in_repo(repo, date)
            regexp=re.compile("#R\S+")
            
            for ctx in changes:
                res= re.findall(regexp, repo.changectx(ctx).description())
                if res:
                    bl_r_ids=map(lambda x:x.strip('#R'), res or [])
                    bl_ids=self.pool.get('scrum.product.backlog').search(cr,uid,[('code','in',bl_r_ids),('project_id','=',project.id)])
                else:
                    bl_ids=[]
                # Búsqueda de ficheros
                files_to_append=[]
                filesctx=repo.changectx(ctx).files()
                for file in filesctx:
                    # Vemos si ya existe el fichero como el que hemos encontrado
                    file_ids=self.pool.get('bl.file').search(cr,uid,[('name','=',file),('project_id','=',project.id)])
                    if not file_ids:
                        # Creamos el fichero
                        vals={
                            'project_id':project.id,
                            'name':file,
                        }
                        files_to_append.append(self.pool.get('bl.file').create(cr,uid,vals))
                    else:
                        # Le añadimos la relacion al backlog
                        for file_id in file_ids:
                            files_to_append.append(file_id)
                
                vals={
                    'project_id':project.id,
                    'name':str(repo.changectx(ctx).rev())+':',
                    'user':repo.changectx(ctx).user(),
                    'description':repo.changectx(ctx).description(),
                    'date':str(datetime.datetime.fromtimestamp(repo.changectx(ctx).date()[0])),
                    'backlog_ids':[(6, 0, bl_ids)],
                    'related_files_ids':[(6, 0, files_to_append)],
                }

                chset_id=self.pool.get('hg.changeset').create(cr,uid,vals)

scrum_project()

class hg_changeset(osv.osv):
    _name = 'hg.changeset'
    _description = 'Mercurial changeset'
    _columns={
        'project_id':fields.many2one('scrum.project', 'Project'),
        'name':fields.char('Rev. number',size=64),
        'user':fields.char('User',size=64),
        'description':fields.char('Description',size=512),
        'date':fields.datetime('Date'),
        'backlog_ids':fields.many2many('scrum.product.backlog',
                                                 'hg_changeset_product_backlog_rel',
                                                 'product_backlog_id',
                                                 'hg_changeset_id',
                                                 'Prod. backlog'),
    }
    _order = "date desc"

    def create(self, cr, uid, vals, context=None):
        if ('backlog_ids' not in vals or not vals['backlog_ids']) :
            pass
        else:
            self.pool.get('scrum.product.backlog').update_files(cr,uid,vals['backlog_ids'][0][2],vals['related_files_ids'][0][2])
        return super(hg_changeset, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        chsets=self.pool.get('hg.changeset').browse(cr,uid,ids)
        for chset in chsets:
            if ('backlog_ids' not in vals or not vals['backlog_ids']) :
                bl_ids = map(lambda x:x.id, chset.backlog_ids or [])
            else:
                bl_ids= vals['backlog_ids'][0][2]
            if  ('related_files_ids' not in vals or not  vals['related_files_ids']) :
                files_ids= map(lambda x:x.id, chset.related_files_ids or [])
            else:
                files_ids=vals['related_files_ids'][0][2]

            self.pool.get('scrum.product.backlog').update_files(cr,uid,bl_ids,files_ids)
        return super(hg_changeset, self).write(cr, uid, ids, vals, context=context)

hg_changeset()


class bl_file(osv.osv):
    _name = 'bl.file'
    _description = 'Product Backlog Files'
    _columns={
        'name':fields.char('File',size=256),
        'project_id':fields.many2one('scrum.project', 'Project'),
        'backlog_ids':fields.many2many('scrum.product.backlog',
                                                 'file_product_backlog_rel',
                                                 'file_id',
                                                 'product_backlog_id',
                                                 'Product backlog'),
        'hg_changeset_ids':fields.many2many('hg.changeset',
                                                 'file_hg_changeset_rel',
                                                 'file_id',
                                                 'hg_changeset_id',
                                                 'Changeset')
    }
bl_file()

class hg_changeset2(osv.osv):

    _inherit = "hg.changeset"

    _columns = {
        'related_files_ids':fields.many2many('bl.file',
                                                 'file_hg_changeset_rel',
                                                 'hg_changeset_id',
                                                 'file_id',
                                                 'Related Files'),
    }

hg_changeset2()


class scrum_product_backlog(osv.osv):
    """Adds new fields to product backlogs"""

    _inherit = 'scrum.product.backlog'
    _columns={
        'code': fields.char('Req. Id', size=12, select=1),
        'related_files_ids':fields.many2many('bl.file',
                                                 'file_product_backlog_rel',
                                                 'product_backlog_id',
                                                 'file_id',
                                                 'Related Files'),
        'hg_changeset_ids':fields.many2many('hg.changeset',
                                                 'hg_changeset_product_backlog_rel',
                                                 'hg_changeset_id',
                                                 'product_backlog_id',
                                                 'Changesets')
    }

    def update_files (self, cr, uid, ids, file_ids):
        bls= self.browse(cr,uid,ids)

        for bl in bls:
            update=False

            files_to_append= map(lambda x:x.id, bl.related_files_ids or [])
            for file_id in file_ids:
                if not file_id in files_to_append:
                    update=True
                    files_to_append.append(file_id)
            if update:
                vals = {'related_files_ids':[(6, 0, files_to_append)]}
                bl.write (vals)

#    def load_files(self, cr, uid, ids, *args):
#        bls= self.browse(cr,uid,ids)
#        for bl in bls:
#            files=[]
#            for f in bl.related_files_ids:
#                files.append(f.name)
#            repo = hg.repository(ui.ui(), bl.project_id.hg_repo_path)
#            search_string="#"+bl.code
#
#            for ctx in repo.changelog:
#                res= repo.changectx(ctx).description().find(search_string)
#                if res != -1:
#                    print repo.changectx(ctx).description()
#                    filesctx=repo.changectx(ctx).files()
#                    for file in filesctx:
#                        if not file in files:
#                            # Vemos si ya existe el fichero como el que hemos encontrado
#                            file_ids=self.pool.get('bl.file').search(cr,uid,[('name','=',file),('project_id','=',bl.project_id.id)])
#                            if not file_ids:
#                                # Creamos el fichero relacionado al backlog
#                                vals={
#                                    'project_id':bl.project_id.id,
#                                    'name':file,
#                                    'backlog_ids':[(6, 0, [bl.id])]
#                                }
#                                self.pool.get('bl.file').create(cr,uid,vals)
#                            else:
#                                # recuperamos el fichero y le añadimos la relacion al backlog
#                                bl_files=self.pool.get('bl.file').browse(cr,uid,file_ids)
#                                for bl_file in bl_files:
#                                    bl_ids=map(lambda x:x.id, bl_file.backlog_ids or [])
#                                    bl_ids.append(bl.id)
#                                    self.pool.get('bl.file').write(cr,uid,bl_file.id,{'backlog_ids':[(6, 0, bl_ids)]})
#
#        return True


scrum_product_backlog()



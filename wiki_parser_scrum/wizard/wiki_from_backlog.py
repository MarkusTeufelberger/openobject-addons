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

from osv import fields
from osv import osv

class wiki_from_backlog (osv.osv_memory):
    _name = 'wiki.from.backlog'
    _columns={
        'bl_id':fields.many2one('scrum.product.backlog', 'User Story')
    }

    def update_wiki(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context):
            bl=wiz.bl_id
            wiki_page_id=self.pool.get('wiki.wiki').search(cr, uid, [('bl_id','=',bl.id),('user_story','=',True)])
            vals={
                'bl_id':bl.id,
                'name':'('+bl.code+') '+bl.name,
                'definition':bl.note,
                'user_story':True,
                'project_id':bl.project_id.id,
            }
            print vals
            if not wiki_page_id:
                self.pool.get('wiki.wiki').create(cr,uid,vals)
            else:
                self.pool.get('wiki.wiki').write(cr,uid,wiki_page_id,vals)

        return { 'type': 'ir.actions.act_window_close' }

wiki_from_backlog()


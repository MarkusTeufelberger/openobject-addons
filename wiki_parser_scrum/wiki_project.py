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
#from datetime import datetime, date, time, timedelta
#import tools

class WikiGroup(osv.osv):
    _inherit = "wiki.groups"
    _columns={
        
    }
WikiGroup()


class Wiki(osv.osv):
    _inherit="wiki.wiki"
    _columns={
        'project_id': fields.many2one('scrum.project', 'Related project'),
        'sprint_id': fields.many2one('scrum.sprint', 'Related sprint'),
        'bl_id': fields.many2one('scrum.product.backlog', 'Related backlog item'),
    }

Wiki()


class History(osv.osv):
    _inherit = "wiki.wiki.history"
    _description = "Wiki History"

    _columns = {
      'name':fields.related('wiki_id','name',type='char', readonly=True, string='Name'),
      'version':fields.integer('Version', readonly=True),
      'project_id':fields.related('wiki_id','project_id',type='many2one', relation='scrum.project', readonly=True, string ="Related project"),
      'wiki_group_id':fields.related('wiki_id','group_id',type='many2one', relation='wiki.groups', readonly=True, string ="Group template"),
    }

    def create(self, cr, uid, vals, context=None):
        history = self.pool.get('wiki.wiki.history')

        hists= history.browse(cr,uid,history.search(cr,uid,[('wiki_id', '=', vals.get('wiki_id'))] ))
        date=0;
        new_version=1;
        last_hist=None
        for hist in hists:
            if hist.create_date > date:

                date= hist.create_date
                last_hist=hist
        if last_hist:
            new_version=last_hist.version+1

        vals['version']=new_version
        result = super(History,self).create(cr, uid, vals, context)
        return result

History()

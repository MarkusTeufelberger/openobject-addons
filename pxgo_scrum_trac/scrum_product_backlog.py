# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Borja López Soilán$
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

from osv import fields, osv


class scrum_product_backlog(osv.osv):
    _inherit = "scrum.product.backlog"

    def _get_trac_url(self, cr, uid, ids, field_name, args, context = {}):
        """return ticket url in Trac composed for trac ticket and project tickets link"""
        res = {}
        for product_backlog_id in self.browse(cr, uid, ids):
            res[product_backlog_id.id] = product_backlog_id.project_id.tickets_trac_url
         
        return res

    def _get_remaining_hours(self, cr, uid, ids, field_name, args, context = {}):
        """Returns remaining hours compute it from tasks"""

        cr.execute('SELECT product_backlog_id, sum(remaining_hours) as r_h FROM project_task WHERE product_backlog_id IN ('+','.join(map(str, ids))+') GROUP BY product_backlog_id')

        task_rem = dict(cr.fetchall())
        res={}
        for id in ids:
            if   task_rem.has_key(id)  :
                res[id] = task_rem[id]
            else:
                res[id] = self.browse(cr, uid, id).initial_estimation

        return res

    _columns = {
        'code': fields.char('Req. Id', size=12, select=1),
        'code_trac': fields.integer('Trac Ticket', required=True, select=1 ),
        'component_name': fields.char('Component', size=128, select=1),
        'remaining_hours':fields.function(_get_remaining_hours, method=True, string='Remaining hours'),
        'state': fields.selection([
                        ('new', 'New'),
                        ('assigned', 'Assigned'),
                        ('accepted', 'Accepted'),
                        ('closed', 'Closed'),
                        ('reopened', 'Reopened')
                    ], 'Status', size=16),
        'initial_estimation': fields.float('Initial estimation'),
        'trac_ticket_url': fields.function(_get_trac_url, type='char', size = 64, method = True, string = "Trac Url"),
    }

    _defaults = {
        'state': lambda *a: 'new'
    }

scrum_product_backlog()

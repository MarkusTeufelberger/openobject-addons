# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Joel Grand-guillaume (Camptocamp)
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

from osv import fields, osv
import netsvc


class project_classification(osv.osv):
    _name = "project.classification"
    _description = "Project classification"
        
    _columns ={
        'name': fields.char('Classification Name', required=True, size=64),
        'project_id':fields.many2one('project.project', 'Parent project', help="The parent\
            project that will be set when choosing this classification in a project.", required=True),
        'to_invoice': fields.many2one('hr_timesheet_invoice.factor', 'Reinvoice Costs',
            help="Fill this field if you plan to automatically generate invoices based " \
            "on the costs in this classification"),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'user_id': fields.many2one('res.users', 'Account Manager'),
        'pricelist_id': fields.many2one('product.pricelist', 'Sale Pricelist',),
    }

project_classification()

class project_project(osv.osv):
    _inherit = "project.project"
    
    def onchange_classification_id(self, cr, uid, ids, classification_id):
        classification = self.pool.get('project.classification').browse(cr,uid,classification_id)
        return {'value':{
                'parent_id': classification.project_id.id,
                'to_invoice': classification.to_invoice.id or False,
                'currency_id': classification.currency_id.id or False,
                'user_id': classification.user_id.id or False,
                'pricelist_id': classification.pricelist_id.id or False,
                }}
    
    _columns ={
        'classification_id':fields.many2one('project.classification', 'Classification', help="This will automatically set the parent "\
        "project as well as other default values define for this kind project (like pricelist, invoice factor,..)", required=True),
    }
    
project_project()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

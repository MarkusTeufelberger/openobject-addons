# -*- encoding: utf-8 -*-
#  c2c_date_in_so_line
#  Created by Nicolas Bessi
#  Copyright (c) 2009 CamptoCamp. All rights reserved.
####################################################################
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
from osv import osv, fields
from mx import DateTime
class sale_order(osv.osv):
    """Override sale.order in order to add a date field"""
    _inherit = "sale.order"
    _columns = {
        'planned_date':fields.date('Planned Delivery date',
                                        readonly=True,
                                        states={'draft':[('readonly',False)]}
                                        )
    }
    ## @param self The object pointer.
    ## @param cr A psycopg cursor.
    ## @param uid res.user.id that is currently loged
    ## @param ids An int or list of int that are equals to an invoice id
    ## @param context a simple dict
    def button_refresh_date(self, cr, uid, ids, context={}):
        """when refresh all of the SO line Date to the one specified in SO"""
        if not ids :
            return False
        planned_date = self.browse(cr, uid, ids[0]).planned_date
        if not planned_date :
            raise osv.except_osv(_('Error !'), 
                                 _('Please fill the Planned delivery date '+
                                 'before using this button')
                                )

        for saleorder in self.browse(cr, uid, ids, context):
            #we modify the requiered data in the line
            for line in saleorder.order_line :
                line.write({'planned_date' : planned_date}, {})
        return True
        
    def action_ship_create(self, cr, uid, ids, *args):
        if not ids :
            return False
        now = DateTime.today()
        for order in self.browse(cr, uid, ids, context={}):
            for line in order.order_line:
                if line.planned_date :
                    delay = 0
                    planDate = DateTime.strptime(
                                            line.planned_date, 
                                            '%Y-%m-%d %H:%M:%S'
                                        )
                                            
                    delta = planDate - now
                    delay = delta.days
                line.write({'delay':delay})
        return super(sale_order, self).action_ship_create(cr, uid, ids, *args)
                    
            
    
    
sale_order()

class sale_order_line(osv.osv):
    """adding date field"""
    _inherit = "sale.order.line"
    _columns = {
        'planned_date':fields.date('Planned Delivery date',
                                        readonly=True,
                                        states={'draft':[('readonly',False)]},
                                        )
    }    
    
sale_order_line()
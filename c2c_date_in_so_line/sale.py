# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
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

from osv import osv, fields
from mx import DateTime
from tools.translate import _

class sale_order(osv.osv):
    """Override sale.order in order to add a date field"""
    _inherit = "sale.order"
    _columns = {
        'soplanned_date':fields.date('SO Planned Delivery date',
                                        readonly=True,
                                        states={'draft':[('readonly',False)]},
                                        help="""Fullfill to force 'Planned delivery Date' in all lines according to 
                                        the selected date (when creating the SO lines). Leave empty to let the system compute lines values. You can
                                        use the button 'Update line planned date' afterwards to force the value once it has 
                                        been computed."""
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
        planned_date = self.browse(cr, uid, ids[0]).soplanned_date
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
                                            '%Y-%m-%d'
                                        )
                                            
                    delta = planDate - now
                    delay = delta.days
                    line.write({'delay':delay})
        return super(sale_order, self).action_ship_create(cr, uid, ids, *args)
                    
            
    
    
sale_order()

class sale_order_line(osv.osv):
    """adding date field"""
    _inherit = "sale.order.line"
    def _default_planned_date(self, cr, uid, context={}) :
        print context
        return context.get('myplanned_date', False)
        
    _columns = {
        'planned_date':fields.date('Planned Delivery date',
                                        readonly=True,
                                        states={'draft':[('readonly',False)]},help="Put the planned delivery date for this lines. This will compute for you the delay to put on the line.",
                                        )
    }    
    _defaults = {'planned_date': _default_planned_date }
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
        uom=False, qty_uos=0, uos=False, name='', partner_id=False,
        lang=False, update_tax=True, date_order=False, packaging=False, 
        fiscal_position=False, flag=False, planned_date=False):
        to_return = super(sale_order_line, self).product_id_change(
            cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging, 
            fiscal_position, flag)
        if not product :
            return to_return
        if planned_date :
            to_return['value']['planned_date'] = planned_date
        else :
            delay = self.pool.get('product.product').browse(cr,uid,product).sale_delay
            date = str(DateTime.now() + DateTime.DateTimeDeltaFromDays(delay))
            to_return['value']['planned_date'] = date
        return to_return
    
sale_order_line()
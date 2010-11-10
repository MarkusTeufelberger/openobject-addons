# -*- encoding: utf-8 -*-
##############################################################################
#
#    This module copyright (C) 2009 Numérigraphe SARL. All Rights Reserved
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

"""
Changes to the objects of the module "sale" to allow fixed delivery dates
"""

import time
from mx import DateTime

from osv import osv, fields
import netsvc

class sale_order(osv.osv):
    """Add the delivery date to the Sale Order object."""
    _inherit = 'sale.order'

    def copy(self, cr, uid, id, default=None, context=None):
        """Make sure the delivery date is not copied along with the Sale Order"""
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['date_delivery'] = False
        return super(sale_order, self).copy(cr, uid, id, default=default,
                                            context=context)        
    _columns = {
        'date_delivery': fields.date('Expected Delivery Date', readonly=True,
            states={'draft': [('readonly', False)]},
            help="""The date when the order should be delivered to the customer.
When Packings are created from this Order, the dispatch date is computed \
from this date and the Company's Security Delay.
Leave this field empty if you want the Packings dispatched as soon as \
possible. In that case the dispatch date is computed using the default \
method - usually from the Product Lead Times and the Company's Security Delay.""",
        ),
    }
sale_order()

class sale_order_line(osv.osv):
    """Redefine the computation of dispatch dates."""
    _inherit = 'sale.order.line'

    def _get_dates_planned(self, cr, uid, ids, context=None):
        """
        Compute the dates when lines should be shipped.
        Uses the delivery date specified in the order, or the product lead time
        as a default.
        
        @param ids: list of Sale Order Line IDs for which you want dates
        @return: a dictionary of dates by line ID
        """
        # Get the default dates using the standard method (lead times) 
        res = super(sale_order_line, self)._get_dates_planned(cr, uid,
            ids, context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        # Compute the dispatch dates for fixed delivery dates
        for line in self.browse(cr, uid, ids, context=context):
            if line.order_id.date_delivery:
                netsvc.Logger().notifyChannel("sale_delivery_date",
                    netsvc.LOG_DEBUG,
                    "Using fixed delivery date %s and Security Lead Time %d for Sale Order Line %d" % (
                        line.order_id.date_delivery,
                        company.security_lead,
                        line.id))
                res[line.id] = (DateTime.strptime(line.order_id.date_delivery , '%Y-%m-%d')
                                - DateTime.DateTimeDeltaFromDays(company.security_lead)
                                ).strftime('%Y-%m-%d %H:%M:%S')
                print res[line.id]
        return res
sale_order_line()

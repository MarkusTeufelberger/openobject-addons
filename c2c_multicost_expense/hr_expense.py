# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camtocamp SA
# @author Joël Grand-Guillaume
# $Id: $
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

from mx import DateTime
import time

from osv import fields, osv
from tools.translate import _

class hr_expense_line(osv.osv):
    _inherit = "hr.expense.line"

    def onchange_product_id(self, cr, uid, ids, product_id, uom_id, employee_id, context={}):
        v={}
        if product_id:
            product=self.pool.get('product.product').browse(cr,uid,product_id, context=context)
            v['name']=product.name
            # Compute based on pricetype of employee company
            pricetype_id = self.pool.get('hr.employee').browse(cr,uid,employee_id).user_id.company_id.property_valuation_price_type.id
            context['currency_id']=self.pool.get('hr.employee').browse(cr,uid,employee_id).user_id.company_id.currency_id.id
            pricetype=self.pool.get('product.price.type').browse(cr,uid,pricetype_id)
            amount_unit=product.price_get(pricetype.field, context)[product.id]
            v['unit_amount']=amount_unit
            if not uom_id:
                v['uom_id']=product.uom_id.id
        return {'value':v}
        
hr_expense_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:




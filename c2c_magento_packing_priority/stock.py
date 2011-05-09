# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Guewen Baconnier. Copyright Camptocamp SA
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

class stock_picking(osv.osv):
    _inherit =  'stock.picking'
    _order = 'priority desc, min_date asc, date asc'

    def _get_priority_selection(self, cr, uid, context=None):
        return self.pool.get('base.sale.payment.type').get_priority_selection(cr, uid, context=context)

    _columns = {
        'priority': fields.selection(_get_priority_selection, 'Priority', select=1)
    }

    _defaults = {
        'priority': lambda self, cr, uid, context=None: self.pool.get('base.sale.payment.type').get_priority_default(cr, uid, context),
    }

    def create(self, cr, uid, vals, context=None):
        if 'sale_id' in vals and vals['sale_id']:
            sale_order_priority = self.pool.get('sale.order').read(cr, uid, vals['sale_id'], ['packing_priority'])
            if 'packing_priority' in sale_order_priority:
                vals['priority'] = sale_order_priority['packing_priority']

        return super(stock_picking, self).create(cr, uid, vals, context)

stock_picking()

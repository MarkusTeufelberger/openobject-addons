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

from osv import osv, fields

class base_sale_payment_type(osv.osv):
    _inherit = 'base.sale.payment.type'

    def get_priority_selection(self, cr, uid, context=None):
        return ('1', 'Low'), ('2', 'Normal'), ('3', 'High')

    def get_priority_default(self, cr, uid, context=None):
        return '2'

    _columns = {
        'packing_priority': fields.selection(get_priority_selection, 'Packing Priority')
    }

    _defaults = {
        'packing_priority': get_priority_default,
    }

base_sale_payment_type()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _get_priority_selection(self, cr, uid, context=None):
        return self.pool.get('base.sale.payment.type').get_priority_selection(cr, uid, context=context)

    _columns = {
        'packing_priority': fields.selection(_get_priority_selection, 'Packing priority')
    }

    _defaults = {
        'packing_priority': lambda self, cr, uid, context=None: self.pool.get('base.sale.payment.type').get_priority_default(cr, uid, context),
    }

    def oe_create(self, cr, uid, vals, data, external_referential_id, defaults, context):
        """ create the sale order with the priority defined in the base sale payment type"""
        if 'ext_payment_method' in vals:
            ext_payment_method = vals['ext_payment_method']
            ext_pay_config = self.payment_code_to_payment_settings(cr, uid, ext_payment_method, context)
            if ext_pay_config:
                vals['packing_priority'] = ext_pay_config.packing_priority or self.pool.get('base.sale.payment.type').get_priority_default(cr, uid, context)
        return super(sale_order, self).oe_create(cr, uid, vals, data, external_referential_id, defaults, context)

sale_order()
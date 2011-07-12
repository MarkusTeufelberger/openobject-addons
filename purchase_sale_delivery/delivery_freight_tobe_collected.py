# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

"""object that allow register the freight to be collected"""

from osv import osv, fields
from tools import config
from tools.translate import _
import time

class delivery_freight_tobe_collected(osv.osv):
    """object that allow register the freight to be collected"""

    _name = 'delivery.freight.tobe.collected'

    def _get_euro(self, cr, uid, context={}):
        """returns the euro id because it is the first currency"""
        try:
            return self.pool.get('res.currency').search(cr, uid, [], order='id')[0]
        except:
            return False

    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'purchase_id': fields.many2one('purchase.order', 'Purchase'),
        'sale_id': fields.many2one('sale.order', 'Sale'),
        'picking_id': fields.many2one('stock.picking', 'Picking'),
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier', required=True),
        'price': fields.float('Price', required=True, digits=(16, int(config['price_accuracy']))),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic account'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True, ondelete='set null')
    }

    _defaults = {
        'price': lambda *a: 0.0,
        'currency_id': _get_euro
    }


    def compute_delivery_price(self, cr, uid, ids, context=None):
        """computes delivery price from carrier and purchase_lines"""
        if context is None: context = {}

        for delivery in self.browse(cr, uid, ids):
            if not delivery.carrier_id:
                raise osv.except_osv(_('Warning'), _('Carrier isn\'t defined.'))

            order = delivery.picking_id or delivery.purchase_id or delivery.sale_id
            model = order._table_name
            address = (delivery.picking_id and delivery.picking_id.address_id) and delivery.picking_id.address_id.id or (delivery.purchase_id and delivery.purchase_id.partner_address_id.id or (delivery.sale_id and delivery.sale_id.partner_shipping_id.id or False))

            if not address:
                raise osv.except_osv(_('No address available !'), _('No shipping address available! Remember to save the line before pressing compute price button!'))

            grid_id = self.pool.get('delivery.carrier').grid_get(cr, uid, [delivery.carrier_id.id], address)
            if not grid_id:
                raise osv.except_osv(_('No grid available !'), _('No grid matching for this carrier !'))

            price = self.pool.get('delivery.grid').get_price(cr, uid, grid_id, order, time.strftime('%Y-%m-%d'))

            self.write(cr, uid, [delivery.id], {'price': price})

        return True

delivery_freight_tobe_collected()
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

"""Inherits account.invoice.line to drag partner discount to invoice lines"""

from osv import osv

class account_invoice_line(osv.osv):
    """Inherits account.invoice.line to drag partner discount to invoice lines"""

    _inherit = 'account.invoice.line'

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, context=None):
        """set partner discount to sale order lines discount"""
        if context is None: context = {}

        result = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom, qty=qty,
                name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit,
                address_invoice_id=address_invoice_id, context=context)

        if partner_id and result.get('value', False) and type == 'out_invoice':
            result['value']['discount'] = self.pool.get('res.partner').browse(cr, uid, partner_id).sale_discount

        return result

account_invoice_line()

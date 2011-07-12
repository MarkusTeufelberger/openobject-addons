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

"""Adds small functionalities for sale.order.line related to shipments"""

from osv import osv, fields

class sale_order_line(osv.osv):
    """Adds small functionalities for sale.order.line related to shipments"""

    _inherit = "sale.order.line"

    _columns = {
        'shipment_line': fields.boolean('Shipment line')
    }

    def unlink(self, cr, uid, ids, context=None):
        """Allow delete shipment lines when it is confirmed"""
        if context is None: context = {}

        for line in self.browse(cr, uid, ids):
            if line.shipment_line and line.state != 'done':
                self.write(cr, uid, [line.id], {'state': 'draft'})

        return super(sale_order_line, self).unlink(cr, uid, ids, context=context)

sale_order_line()

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Santiago Argüeso Armesto$
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

"""inherits stock.production lot improving the management of production lot sequences"""

from osv import osv, fields
import time

class serial_number(osv.osv):
    _name = 'serial.number'
    _description = 'Serial number'

    def make_sscc(self, cr, uid, context=None):
        """return serial number"""
        if context is None: context = {}
        if context.get('product_id'):
            sequence_obj_id = self.pool.get('product.product').browse(cr, uid, context['product_id']).sequence_sn_id
            if sequence_obj_id:
                sequence_id = sequence_obj_id.id
                sequence_number = self.pool.get('ir.sequence').get_id(cr, uid, sequence_id)
                return sequence_number

        sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.serial')
        return sequence

    _columns = {
        'name': fields.char('Serial', size=64, required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'date': fields.datetime('Created Date', required=True, readonly=True),
        'move_ids':fields.many2many('stock.move', 'serial_move_rel', 'sn_id','move_id', 'Stock moves')
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'name': make_sscc,
        'product_id': lambda x, y, z, c: c.get('product_id', False),
    }

    _sql_constraints = [
        ('name_ref_uniq', 'unique (name,product_id)', 'The serial/ref must be unique !'),
    ]

serial_number()


# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2009 Àngel Àlvarez - NaN  (http://www.nan-tic.com) All Rights Reserved.
#
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


from osv import fields, osv
from tools.translate import _

class stock_move(osv.osv):
    _inherit = 'stock.move'

    def onchange_location_id(self, cr, uid, ids, location_id, context):
        """
        Fill in automatically product and lot if source location is restricted.
        """
        if not location_id:
            return {}
        values = {}
        filter_ids = self.pool.get('stock.report.prodlots').search(cr, uid, [
            ('location_id','=',location_id),
        ])
        if len(filter_ids) == 1:
            record = self.pool.get('stock.report.prodlots').browse(cr, uid, filter_ids[0])
            values['product_id'] = record.product_id and record.product_id.id or False
            values['prodlot_id'] = record.prodlot_id and record.prodlot_id.id or False
        return {'value': values}

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, address_id=False):
        """
        Fill in automatically production lot if there is only when lot in the given location and product.
        """
        result = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id, loc_id, loc_dest_id, address_id)
        if not loc_id or not prod_id:
            return result

        values = {}
        filter_ids = self.pool.get('stock.report.prodlots').search(cr, uid, [
            ('location_id','=',loc_id),
            ('product_id','=',prod_id),
        ])
        if len(filter_ids) == 1:
            record = self.pool.get('stock.report.prodlots').browse(cr, uid, filter_ids[0])
            values['prodlot_id'] = record.prodlot_id and record.prodlot_id.id or False

        if not 'value' in result:
            result['value'] = {}
        result['value'].update( values )
        return result
stock_move()

class stock_location(osv.osv):
    _inherit = 'stock.location'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        active_type = context.get('active_type')
        active_product_id = context.get('active_product_id')
        active_prodlot_id = context.get('active_prodlot_id')
        if active_type == 'source' and ( active_product_id or active_prodlot_id ):
            domain = []
            if active_prodlot_id:
                domain.append( ('prodlot_id','=',active_prodlot_id) )
            if active_product_id:
                domain.append( ('product_id','=',active_product_id) )

            filter_ids = []
            ids = self.pool.get('stock.report.prodlots').search(cr, uid, domain, context=context)
            for record in self.pool.get('stock.report.prodlots').browse(cr, uid, ids, context):
                filter_ids.append( record.location_id.id )
            args = args[:]
            args.append( ('id','in',filter_ids) )
        return super(stock_location, self).search(cr, uid, args, offset, limit, order, context, count)
stock_location()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

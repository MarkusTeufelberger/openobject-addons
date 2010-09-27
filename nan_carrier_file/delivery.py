# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010   Àngel Àlvarez 
#                      NaN Projectes de programari lliure S.L.
#                      (http://www.nan-tic.com) All Rights Reserved.
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


from osv import fields,osv
from tools.translate import _
import netsvc


class carrier_file_wizard( osv.osv_memory ):
    _name ='carrier.file.wizard'

    _columns = {
        'start_date': fields.datetime( 'Start Date' ),
        'end_date': fields.datetime('End Date' ),
        'carrier_id': fields.many2one( 'delivery.carrier', 'Carrier' )  
    }

    def action_accept( self, cr, uid, ids, context=None ):
        if context == None:
            context ={}
        
        wizard = self.pool.get('carrier.file.wizard').browse( cr, uid, ids[0], context=context )
        filter = []
        if wizard.start_date:
            filter.append( ('date_done','>=',wizard.start_date) )
        if wizard.end_date:
            filter.append( ('date_done','<=',wizard.end_date) )

        filter.append( ( 'state', '=', 'done' ) )
        filter.append( ( 'type', '=', 'out' ) )
        picking_ids =  self.pool.get('stock.picking').search(cr, uid, filter, context=context) 
        
        self.pool.get('delivery.carrier').gen_carrier_files( cr, uid, picking_ids, None, context )
        return  {}

carrier_file_wizard()
	

class delivery_carrier( osv.osv ):
    _inherit = 'delivery.carrier'

    _columns = {
        'format_id': fields.many2one('file.format', 'File Format' ),
    }

    def gen_carrier_files( self, cr, uid, picking_ids, carrier_id, context=None ):
        if context == None:
            context ={}

        picking_carriers = {}
        for picking in self.pool.get('stock.picking').browse(cr, uid, picking_ids, context ):
            if picking.type != 'out':
                continue
            if not picking_carriers.get( picking.carrier_id.id , False ):
                picking_carriers[ picking.carrier_id.id ] = [ picking.id ]
            else:
                picking_carriers[ picking.carrier_id.id ].append( picking.id )

        if carrier_id == None:
            for carrier in picking_carriers:
                self.pool.get('file.format').export_file( cr, uid, picking.carrier_id and picking.carrier_id.format_id and picking.carrier_id.format_id.id, picking_carriers[carrier], context )
        else:
            self.pool.get('file.format').export_file( cr, uid, picking.carrier_id.format_id.id, picking_carriers[carrier_id], context )

delivery_carrier()


class stock_picking( osv.osv ):
    _inherit = 'stock.picking'

    def action_done( self, cr, uid, ids, context=None ):
        result = super( stock_picking,self ).action_done( cr, uid, ids, context=context )
        self.pool.get( 'delivery.carrier' ).gen_carrier_files( cr, uid, ids, None, context ) 
        return result

stock_picking()
 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

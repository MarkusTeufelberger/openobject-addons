# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
    Inherit Stock to add more fields in Stock object.
"""

from osv import osv, fields
import netsvc
import time
from mx import DateTime
import ir
from tools import config
from tools.translate import _
import tools


class stock_picking(osv.osv):
    _name='stock.picking'
    _inherit='stock.picking'
    
    _columns={
                'bl_no' : fields.char('BL No.', size=64,),
                'vessel_name' : fields.char('Vessel Name', size=128,),
                'voyage_number' : fields.char('Voyage Number', size=64,),
                'shipping_company' : fields.char('Shipping Company', size=128,),
                'departure_date' : fields.char('Departure Date', size=64),
                'arrival_date' : fields.char('Arrival Date', size=64),
                'port_of_departure' : fields.many2one('stock.location','Depart From'),
                'port_of_arrival' : fields.many2one('stock.location','Destination'),
                'myfab_description' : fields.text('Description',),
                'container_id' : fields.char('Container ID', size=128,),
                'container_seal' : fields.char('Nr Container Seal', size=128,),
                'loading_code' : fields.char('Loading Code', size=128,),             
              
              }
stock_picking()

class stock_move(osv.osv):
    _inherit="stock.move"
    
    def action_confirm(self, cr, uid, ids, context={}):
#        ids = map(lambda m: m.id, moves)
        moves = self.browse(cr, uid, ids)
        n_moves=[]
        n_ids=[]
        for m in moves:
            if m.state=='assigned':
                n_moves.append(m)
                n_ids.append(m.id)
        self.write(cr, uid, n_ids, {'state':'confirmed'})
        i=0
        def create_chained_picking(self,cr,uid,moves,context):
            new_moves=[]
            if moves:
                picking=moves[0].picking_id
          
                if picking.purchase_id.routing_id:
                    routing_sequence=picking.purchase_id.routing_id.segment_sequence_ids
                    count=0
                    for r_seq in routing_sequence:
                        count=count+1
                        loc=r_seq.port_of_loading
                        dest_loc=r_seq.port_of_destination
                        delay=r_seq.chained_delay
                        po=picking.purchase_id.name
                        sequence=r_seq.sequence
                        routing_id=picking.purchase_id.routing_id
                     
                        ptype = self.pool.get('stock.location').picking_type_get(cr, uid, loc, dest_loc)
                        pickid = self.pool.get('stock.picking').create(cr, uid, {
                        'name': picking.name,
                        'origin': str(picking.origin or ''),
                        'type': ptype,
                        'note': picking.note,
                        'move_type': picking.move_type,
                        'address_id': picking.address_id.id,
                        'invoice_state': 'none'
                    })
                    
                        new_moves=[]
                        for m in moves:
                            
                            new_id = self.pool.get('stock.move').copy(cr, uid, m.id, {
                            'location_id': loc.id,
                            'location_dest_id': dest_loc.id,
                            'date_moved': time.strftime('%Y-%m-%d'),
                            'picking_id': pickid,
                            'state':'waiting',
                            'move_history_ids':[],
                            'date_planned': (DateTime.strptime(m.date_planned, '%Y-%m-%d %H:%M:%S') + DateTime.RelativeDateTime(days=delay or 0)).strftime('%Y-%m-%d'),
                            'move_history_ids2':[]}
                        )
                            
                            if count<=len(routing_sequence):
                                self.pool.get('stock.move').write(cr, uid, [m.id], {
                                    'move_dest_id': new_id,
                                    'move_history_ids': [(4, new_id)]
                                })
                                new_moves.append(self.browse(cr, uid, [new_id])[0])
                               
                           # m=self.pool.get('stock.move').browse(cr,uid,[new_id])[0]
                        moves=[]
                        moves=new_moves
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'stock.picking', pickid, 'button_confirm', cr)
                        
                
        create_chained_picking(self, cr, uid, n_moves, context)
        return []
stock_move()

class stock_routing(osv.osv):
    _name='stock.routing'
    _columns={
              'name': fields.char('Routing Name',size=256,required=True),
              'description': fields.char('Description',size=256),
              'kind_transport': fields.selection([('By air','By Air'),('By sea','By Sea'),('By road','By Road')],'Kind Of Transport'),
              'port_of_loading': fields.many2one('stock.location','Incoming Goods Location'),
             'segment_sequence_ids': fields.one2many('segment.sequence','routing_id','Segment Sequence')
              }
    
    def create(self, cr, user, vals, context=None):
      incoming_loc=vals['port_of_loading']
      seg_ids=vals['segment_sequence_ids']
      counter=0
      flag=0
      for segments in seg_ids:    
          segment=segments[2]
          if counter==0:
              if segment['port_of_loading']<>incoming_loc:
                  flag=1
              else:
                  prev_dest=segment['port_of_destination']
                  counter=counter+1
          else:
              if segment['port_of_loading']<>prev_dest:
                  flag=1
              else:
                  prev_dest=segment['port_of_destination']
                  counter=counter+1
            
      if flag==1:
           raise osv.except_osv(_('Error !'), _('Routing Is Not Well Defined'))
                  
      cr_id=super(osv.osv,self).create(cr,user,vals,context)
      return cr_id
    
stock_routing()

class segment_sequence(osv.osv):
    _name='segment.sequence'
    _columns={
              'sequence': fields.integer('Sequence'),
              'name': fields.char('Segment Name', size=256),
              'port_of_loading': fields.many2one('stock.location','Depart From',required=True),
              'port_of_destination': fields.many2one('stock.location','Destination',required=True),
              'kind_transport': fields.selection([('By air','By Air'),('By sea','By Sea'),('By road','By Road')],'Kind Of Transport'),
              'chained_delay': fields.integer('Chained Delay (days)'),
              'routing_id': fields.many2one('stock.routing','Routing'),
              }
    
segment_sequence()
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
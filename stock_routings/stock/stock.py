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
    
    def _set_minimum_date(self, cr, uid, ids, name, value, arg, context):
        if not value: return False
        if isinstance(ids, (int, long)):
            ids=[ids]
        for pick in self.browse(cr, uid, ids, context):
            sql_str="""update stock_move set
                    date_planned='%s'
                where
                    picking_id=%s """ % (value,pick.id)
            if pick.min_date:
                sql_str += " and (date_planned='"+pick.min_date+"' or date_planned<'"+value+"')"
            cr.execute(sql_str)
        return True
    
    def get_min_max_date(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for id in ids:
            res[id] = {'min_date':False, 'max_date': False}
        if not ids:
            return res
        cr.execute("""select
                picking_id,
                min(date_planned),
                max(date_planned)
            from
                stock_move
            where
                picking_id in (""" + ','.join(map(str, ids)) + """)
            group by
                picking_id""")
        for pick, dt1,dt2 in cr.fetchall():
            res[pick]['min_date'] = str(dt1).split(' ')[0]
            res[pick]['max_date'] = dt2

        return res
    
    
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
                'stock_history_lines' : fields.one2many('stock.history','history_id','History',readonly=True),
                'state': fields.selection([
                    ('draft', 'Draft'),
                    ('auto', 'Waiting1'),
#                   ('confirmed', 'On The Way'),
                    ('confirmed','Confirmed'),
                    ('assigned', 'Available'),
                    ('flottant', 'Floating'),
                    ('underway', 'Underway'),
                    ('unproduction', 'In Production'),
                    ('done', 'Received'),
                    ('cancel', 'Cancel'),
                    ], 'Status', readonly=True, select=True),
                'min_date': fields.function(get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date",
                 method=True,store=True, type='date', string='Planned Date', select=1),
                'sequence_id': fields.many2one('ir.sequence','Sequence'),
              }
stock_picking()

class stock_move(osv.osv):
    _inherit="stock.move"
    
    _columns={
              'state': fields.selection([('draft','Draft'),('waiting','Waiting'),('confirmed','Confirmed'),('assigned','Available'),('done','Received'),('cancel','Canceled')], 'Status', readonly=True, select=True),
              'product_qty': fields.float('Quantity', required=True,states={'confirmed': [('readonly', True)],'assigned': [('readonly', True)],'flottant': [('readonly', True)],'underway': [('readonly', True)],'unproduction': [('readonly', True)],'cancel': [('readonly', True)]}),
#              'date_planned': fields.date('Date', required=True, help="Scheduled date for the movement of the products or real date if the move is done."),
              }
    
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
                        'invoice_state': 'none',
                        'port_of_departure': r_seq.port_of_loading.id,
                        'port_of_arrival': r_seq.port_of_destination.id,
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
                            'date_planned': (DateTime.strptime(m.date_planned, '%Y-%m-%d %H:%M:%S') + DateTime.RelativeDateTime(days=delay or 0)).strftime('%Y-%m-%d %H:%M:%S'),
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
              'id':fields.integer('id'),
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
      context.setdefault('id',cr_id)
      return cr_id
  
    def write(self,cr,uid,ids,vals,context=None):
        routing_data=self.read(cr,uid,ids,['port_of_loading','segment_sequence_ids'])
        if vals.__contains__('port_of_loading'):
            port_loading=vals['port_of_loading']
            context['port_of_loading']=port_loading
           
            if vals.__contains__('segment_sequence_ids'):
                segment_seq_id=vals['segment_sequence_ids']
        else:
            if context.__contains__('port_of_loading'):
                port_loading=context['port_of_loading']
                if vals.__contains__('segment_sequence_ids'):
                    segment_seq_id=vals['segment_sequence_ids']
            else:
                port_loading=routing_data[0]['port_of_loading'][0]    
        
        seg_ids=routing_data[0]['segment_sequence_ids']
        if seg_ids:
            if context.has_key('port_of_loading'):
                context.__delitem__('port_of_loading')
            seg_seq_obj=self.pool.get('segment.sequence').read(cr,uid,seg_ids,[])
          
            counter=0
            flag=0
            for segments in seg_seq_obj:
                segment=segments
                if counter==0:
                    if vals['segment_sequence_ids'] and segment['id']==vals['segment_sequence_ids'][0][1]:
                        if port_loading<>vals['segment_sequence_ids'][0][2]['port_of_loading']:
                            flag=1
                        else:
                            prev_dest=vals['segment_sequence_ids'][0][2]['port_of_destination']
                            counter=counter+1
                    else:
                        if port_loading<>segment['port_of_loading'][0]:
                            flag=1
                        else:
                            prev_dest=segment['port_of_destination'][0]
                            counter=counter+1
                else:
                    if vals['segment_sequence_ids'] and segment['id']==vals['segment_sequence_ids'][0][1]:
                         if vals['segment_sequence_ids'][0][2]['port_of_loading']<>prev_dest:
                            flag=1
                         else:
                            prev_dest=vals['segment_sequence_ids'][0][2]['port_of_destination']
                            counter=counter+1
                    else:
                      #  prev_dest=segment['port_of_destination'][0]
                        if segment['port_of_loading'][0]<>prev_dest:
                            flag=1
                        else:
                            prev_dest=segment['port_of_destination'][0]
                            counter=counter+1
            if flag==1:
                raise osv.except_osv(_('Error !'), _('Routing Is Not Well Defined'))
        elif segment_seq_id:
            if not segment_seq_id[0][2]['port_of_loading']==port_loading:
                raise osv.except_osv(_('Error !'), _('Routing Is Not Well Defined'))
        return super(osv.osv,self).write(cr,uid,ids,vals,context)
    
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
    
    def get_id(self,cr,uid,context):
        return context.get('routing_id',False)
    
    def get_location(self,cr,uid,context):
        #for etiny this works properly and gives previous segments port of departure 
        #location in current segments port of loading location, but in gtk it doesn't 
        #work and in gtk user have to manually set the location.
        if context.has_key('client'):  
            if context.__contains__('routing_id'):
                routing_id=context['routing_id']
                segment_ids=self.search(cr,uid,[('routing_id','=',routing_id)])
                
                if segment_ids:
                    segments=self.browse(cr,uid,segment_ids)
                    dest=segments[len(segments)-1].port_of_destination.id
                    context['port_of_loading']=dest
                    return dest
        else:
            context['port_of_loading']=False
            return context.get('port_of_loading',False)
        
        return context.get('port_of_loading',False)
        
        
    _defaults={
                'routing_id': get_id,
                'port_of_loading': get_location, 
               }
    
segment_sequence()

class stock_history(osv.osv):
    _name='stock.history'
    _columns={
              'date': fields.date('Date'),
              'prev_plan_date': fields.date('Previous Planned Date'),
              'new_plan_date': fields.date('New Planned Date'),
              'user': fields.char('User',size=128),
              'description': fields.char('Description/Explanation',size=256),
              'history_id': fields.many2one('stock.picking','History'),   
              }
    
stock_history()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
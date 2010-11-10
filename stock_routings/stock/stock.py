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
import datetime
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
                'bl_no' : fields.char('BL No / HAWB / CMR', size=64,),
                'vessel_name' : fields.char('Vessel Name', size=128,),
                'voyage_number' : fields.char('Voyage Number', size=64,),
                'shipping_company' : fields.char('Shipping Line', size=128,),
                'kind_transport': fields.selection([('Stock move','Stock Move'),('By air','By Air'),('By sea','By Sea'),('By road','By Road'),('By feeder', 'By Feeder')],'Transportation Type', required=True),
#                'forwarder' : fields.many2one('res.partner','Forwarder agent'),
                'forwarder' : fields.char('Forwarder agent', size=128),
                'departure_date' : fields.date('Estimated Time of Departure'),
                'arrival_date' : fields.date('Estimated Time of Arrival'),
                'port_of_departure' : fields.many2one('stock.location','Depart From'),
                'port_of_arrival' : fields.many2one('stock.location','Destination'),
                'myfab_description' : fields.text('Description',),
                'container_id' : fields.char('Container ID', size=128,),
                'container_seal' : fields.char('Nr Container Seal', size=128,),
                'loading_code' : fields.char('Loading Code', size=128,),
                'tracking_number' : fields.char('Tracking Number', size=128),
                'forwarder_ref' : fields.char('Forwarder reference', size=128),
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
                'picking_date' : fields.date('Picking Date', help="Date when actual picking is done by user.",states={'done':[('readonly',True)]}),
                'system_date' : fields.datetime('System Date',readonly=True),
              }
    
    def copy(self, cr, uid, id, default=None, context={}):
        if default is None:
            default = {}
        default = default.copy()
        default['stock_history_lines']=[]
        default['backorder_id'] = False
        return super(stock_picking,self).copy(cr,uid,id,default,context)    
    
stock_picking()

def date_difference(cr,uid,old_date,new_date):
    final_old_dt=old_date.split(' ')
    final_new_dt=new_date.split(' ')
    old_dt=final_old_dt[0].split('-')
    new_dt=final_new_dt[0].split('-')
    old_yy,old_mm,old_dd=old_dt[0],old_dt[1],old_dt[2]
    new_yy,new_mm,new_dd=new_dt[0],new_dt[1],new_dt[2]
    days_delay=datetime.date(int(new_yy),int(new_mm),int(new_dd))-datetime.date(int(old_yy),int(old_mm),int(old_dd))
    
    return days_delay.days

class stock_move(osv.osv):
    _inherit="stock.move"
    
    _columns={
              'picking_date' : fields.date('Picking Date'),
              'container_id' : fields.char('Container id / Box id', size=128,),
              'state': fields.selection([('draft','Draft'),('waiting','Waiting'),('confirmed','Confirmed'),('assigned','Available'),('done','Received'),('cancel','Canceled')], 'Status', readonly=True, select=True),
              'product_qty': fields.float('Quantity', required=True,states={'confirmed': [('readonly', True)],'assigned': [('readonly', True)],'flottant': [('readonly', True)],'underway': [('readonly', True)],'unproduction': [('readonly', True)],'cancel': [('readonly', True)]}),
              'date_planned': fields.date('Date', required=True, help="Scheduled date for the movement of the products or real date if the move is done."),
              }
    
    def action_confirm(self, cr, uid, ids, context={}):
#        ids = map(lambda m: m.id, moves)
        moves = self.browse(cr, uid, ids)
        n_moves=[]
        n_ids=[]
        for m in moves:
            if m.state=='assigned' or m.state=='draft':
                n_moves.append(m)
                n_ids.append(m.id)
        self.write(cr, uid, n_ids, {'state':'confirmed'})
        i=0
        def create_chained_picking(self,cr,uid,moves,context):
            new_moves=[]
            if moves and moves[0].picking_id.type!='out':
                picking=moves[0].picking_id
                if context.has_key('routing_id') and context['routing_id']:
                    routing_data=self.pool.get('stock.routing').browse(cr,uid,context['routing_id'])
                    routing_sequence=routing_data.segment_sequence_ids
                    
                    count=0
                    for r_seq in routing_sequence:
                        count=count+1
                        loc=r_seq.port_of_loading
                        dest_loc=r_seq.port_of_destination
                        delay=r_seq.chained_delay
                        po=picking.purchase_id.name
                        sequence=r_seq.sequence
                        routing_id=routing_data.id
                    
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
                        'kind_transport': r_seq.kind_transport
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
                    
                elif picking.purchase_id.routing_id:
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
                        'kind_transport': r_seq.kind_transport
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
                        
                elif moves[0] and moves[0].purchase_line_id and moves[0].purchase_line_id.order_id and moves[0].purchase_line_id.order_id.routing_id:
                    routing_sequence=moves[0].purchase_line_id.order_id.routing_id.segment_sequence_ids
                    if moves[0].location_id and moves[0].location_dest_id:
                        first_location_id=moves[0].location_id.id
                        first_dest_location_id=moves[0].location_dest_id.id
                    count=0
                    this_move=False
                    for r_seq in routing_sequence:                        
                        count=count+1
                        if this_move:
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
                            'kind_transport': r_seq.kind_transport
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
                        
                        if r_seq.port_of_loading.id==first_location_id and r_seq.port_of_destination.id==first_dest_location_id:
                            this_move=True
                else:
                    all_move_ids=[]
                    for mv in moves:
                        all_move_ids.append(mv.id)
#                    if all_move_ids:
#                        self.pool.get('stock.move').write(cr, uid, all_move_ids, {'state': 'assigned'})
           
        create_chained_picking(self, cr, uid, n_moves, context)
        return []
    
    def action_done(self, cr, uid, ids, context=None):
        track_flag = False
        for move in self.browse(cr, uid, ids):
            if move.move_dest_id.id and (move.state != 'done'):
                cr.execute('insert into stock_move_history_ids (parent_id,child_id) values (%s,%s)', (move.id, move.move_dest_id.id))
                if move.move_dest_id.state in ('waiting', 'confirmed'):
                    self.write(cr, uid, [move.move_dest_id.id], {'state': 'assigned'})
                    if move.move_dest_id.picking_id:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
                    else:
                        pass
                        # self.action_done(cr, uid, [move.move_dest_id.id])
                    if move.move_dest_id.auto_validate:
                        self.action_done(cr, uid, [move.move_dest_id.id], context=context)

            #
            # Accounting Entries
            #
            acc_src = None
            acc_dest = None
            if move.location_id.account_id:
                acc_src = move.location_id.account_id.id
            if move.location_dest_id.account_id:
                acc_dest = move.location_dest_id.account_id.id
            if acc_src or acc_dest:
                test = [('product.product', move.product_id.id)]
                if move.product_id.categ_id:
                    test.append( ('product.category', move.product_id.categ_id.id) )
                if not acc_src:
                    acc_src = move.product_id.product_tmpl_id.\
                            property_stock_account_input.id
                    if not acc_src:
                        acc_src = move.product_id.categ_id.\
                                property_stock_account_input_categ.id
                    if not acc_src:
                        raise osv.except_osv(_('Error!'),
                                _('There is no stock input account defined ' \
                                        'for this product: "%s" (id: %d)') % \
                                        (move.product_id.name,
                                            move.product_id.id,))
                if not acc_dest:
                    acc_dest = move.product_id.product_tmpl_id.\
                            property_stock_account_output.id
                    if not acc_dest:
                        acc_dest = move.product_id.categ_id.\
                                property_stock_account_output_categ.id
                    if not acc_dest:
                        raise osv.except_osv(_('Error!'),
                                _('There is no stock output account defined ' \
                                        'for this product: "%s" (id: %d)') % \
                                        (move.product_id.name,
                                            move.product_id.id,))
                if not move.product_id.categ_id.property_stock_journal.id:
                    raise osv.except_osv(_('Error!'),
                        _('There is no journal defined '\
                            'on the product category: "%s" (id: %d)') % \
                            (move.product_id.categ_id.name,
                                move.product_id.categ_id.id,))
                journal_id = move.product_id.categ_id.property_stock_journal.id
                if acc_src != acc_dest:
                    ref = move.picking_id and move.picking_id.name or False
                    product_uom_obj = self.pool.get('product.uom')
                    default_uom = move.product_id.uom_id.id
                    q = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
                    if move.product_id.cost_method == 'average' and move.price_unit:
                        amount = q * move.price_unit
                    else:
                        amount = q * move.product_id.standard_price

                    date = time.strftime('%Y-%m-%d')
                    partner_id = False
                    if move.picking_id:
                        partner_id = move.picking_id.address_id and (move.picking_id.address_id.partner_id and move.picking_id.address_id.partner_id.id or False) or False
                    lines = [
                            (0, 0, {
                                'name': move.name,
                                'quantity': move.product_qty,
                                'product_id': move.product_id and move.product_id.id or False,
                                'credit': amount,
                                'account_id': acc_src,
                                'ref': ref,
                                'date': date,
                                'partner_id': partner_id}),
                            (0, 0, {
                                'name': move.name,
                                'product_id': move.product_id and move.product_id.id or False,
                                'quantity': move.product_qty,
                                'debit': amount,
                                'account_id': acc_dest,
                                'ref': ref,
                                'date': date,
                                'partner_id': partner_id})
                    ]
                    self.pool.get('account.move').create(cr, uid, {
                        'name': move.name,
                        'journal_id': journal_id,
                        'line_id': lines,
                        'ref': ref,
                    })
        
        segments=False
        final_delay=0
        stock_obj=self.pool.get('stock.picking')
        stock_history_obj=self.pool.get('stock.history')
        purchase_obj=self.pool.get('purchase.order')
        
        user_obj=self.pool.get('res.users')
        user=user_obj.read(cr,uid,uid,['name'])['name']
        current_date=time.strftime('%Y-%m-%d %H:%M:%S')
        move_dates=self.read(cr,uid,ids,['date_planned','picking_id','move_dest_id'])
        first_pick_date=False
        if move_dates:
            if move_dates[0]['picking_id']:
                old_date=stock_obj.read(cr,uid,move_dates[0]['picking_id'][0],['min_date','picking_date'])
                if old_date:
                    old_planned_date=old_date['min_date']
                    old_pick_date=old_date['picking_date']
                    previous_pick_date=old_pick_date
                    first_pick_date=old_pick_date

        move_ids=[]
        move_ids=map(lambda x: x ,ids)
        all_pick_ids=[]
        next_move_ids=[]
        
        for mv_id in move_ids:
            move_dt=self.read(cr,uid,mv_id,['date_planned','picking_id','move_dest_id'])
            if move_dt['picking_id'] and not all_pick_ids.__contains__(move_dt['picking_id'][0]) :
                
                if move_dt['picking_id'][0]!=move_dates[0]['picking_id'][0]:
                    all_pick_ids.append(move_dt['picking_id'][0])
            if move_dt['move_dest_id']:
                move_ids.append(move_dt['move_dest_id'][0])
                next_move_ids.append(move_dt['move_dest_id'][0])
        
        for next_mv_id in next_move_ids:
            next_move_dt=self.browse(cr,uid,next_mv_id)
            if next_move_dt:
                segments=next_move_dt.purchase_line_id.order_id.routing_id.segment_sequence_ids
                source_loc=next_move_dt.location_id
                dest_loc=next_move_dt.location_dest_id
                if segments:
                    for seg in segments:
                        seg_loc=seg.port_of_loading
                        seg_dest_loc=seg.port_of_destination
                        delay=seg.chained_delay
                        if source_loc.id==seg_loc.id and dest_loc.id==seg_dest_loc.id:
                            final_delay=delay
#            purchase_id=stock_obj.read(cr,uid,next_move_dt['picking_id'],['purchase_id'])
#            print 'purchase_id---------------',purchase_id
            main_move=self.search(cr,uid,[('move_dest_id','=',next_mv_id)])
            main_move_data=self.read(cr,uid,main_move,['date_planned','picking_id'])
            picking_date=stock_obj.read(cr,uid,main_move_data[0]['picking_id'][0],['picking_date'])
            if not picking_date['picking_date']:
                previous_date_planned=main_move_data[0]['date_planned']
            else:
                previous_date_planned=str(picking_date['picking_date'])+' 00:00:00'
            new_move_date=(DateTime.strptime(previous_date_planned, '%Y-%m-%d %H:%M:%S') + DateTime.RelativeDateTime(days=final_delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
            self.write(cr,uid,next_mv_id,{'date_planned':new_move_date})
           
        res=[]
        if all_pick_ids:
            cr.execute("""select
                    picking_id,
                    min(date_planned),
                    max(date_planned)
                from
                    stock_move
                where
                    picking_id in (""" + ','.join(map(str, all_pick_ids)) + """)
                group by
                    picking_id""")
            for pick, dt1,dt2 in cr.fetchall():
               
                r={}
                r['id']=pick
                r['min_date'] = dt1
                r['max_date'] = dt2
                res.append(r)
            
            for r in res:
                old_pick_data=stock_obj.read(cr,uid,r['id'],['min_date','state'])
                old_pick_date=old_pick_data['min_date']
                state=old_pick_data['state']
                if state<>'done' and str(old_pick_date)+' 00:00:00' <> r['min_date']:
                    vals={}
                    vals['date']=time.strftime('%Y-%m-%d')
                    vals['prev_plan_date']=old_pick_date
                    vals['new_plan_date']=r['min_date']
                    vals['user']=user
                    vals['history_id']=r['id']
                    history_id=stock_history_obj.create(cr,uid,vals,context=context)
                    
                    stock_obj.write(cr,uid,r['id'],{'min_date':r['min_date']}) 
             
        self.write(cr, uid, ids, {'state': 'done','picking_date':first_pick_date})
        
        if move_dates and move_dates[0]['picking_id']:
            stock_obj.write(cr,uid,move_dates[0]['picking_id'][0],{'system_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_trigger(uid, 'stock.move', id, cr)
        return True
    
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
          if vals.has_key('segment_sequence_ids'):
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
                    if vals.__contains__('segment_sequence_ids') and vals['segment_sequence_ids'] and segment['id']==vals['segment_sequence_ids'][0][1]:
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
                    if vals.__contains__('segment_sequence_ids') and vals['segment_sequence_ids'] and segment['id']==vals['segment_sequence_ids'][0][1]:
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
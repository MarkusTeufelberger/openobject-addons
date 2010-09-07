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

from osv import osv,fields
import netsvc


def _incoterm_get(self, cr, uid, context={}):
    cr.execute('select code, code||\', \'||name from stock_incoterms where active')
    return cr.fetchall()

class purchase_order(osv.osv):
    _name='purchase.order'
    _inherit='purchase.order'
    
    def _set_minimum_planned_date(self, cr, uid, ids, name, value, arg, context):
        if not value: return False
        if type(ids)!=type([]):
            ids=[ids]
        for po in self.browse(cr, uid, ids, context):
            cr.execute("""update purchase_order_line set
                    date_planned=%s
                where
                    order_id=%s and
                    (date_planned=%s or date_planned<%s)""", (value,po.id,po.minimum_planned_date,value))
        return True
    
    def _minimum_planned_date(self, cr, uid, ids, field_name, arg, context):
        res={}
        purchase_obj=self.browse(cr, uid, ids, context=context)
        for purchase in purchase_obj:
            res[purchase.id] = False
            if purchase.order_line:
                min_date=purchase.order_line[0].date_planned
                for line in purchase.order_line:
                    if line.date_planned < min_date:
                        min_date=line.date_planned
                res[purchase.id]=str(min_date).split(' ')[0]
        return res
    
    _columns={
              'state': fields.selection([
#                           ('draft', 'Request for Quotation'), 
                            ('draft', 'Draft'), 
                            ('rfq', 'Request for Quotation'), 
                            ('wait', 'Waiting'), 
                            ('confirmed', 'Confirmed'), 
                            ('approved', 'Approved'),
                            ('except_picking', 'Shipping Exception'), 
                            ('except_invoice', 'Invoice Exception'), 
                            ('done', 'Done'), 
                            ('cancel', 'Cancelled')], 
                        'Order Status', 
                        readonly=True, 
                        help="The state of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' state. Then the order has to be confirmed by the user, the state switch to 'Confirmed'. Then the supplier must confirm the order to change the state to 'Approved'. When the purchase order is paid and received, the state becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the state becomes in exception.", 
                        select=True),
            'port_of_loading': fields.many2one('stock.location','Depart From'),
            'port_of_destination': fields.many2one('stock.location','Destination'),
            'kind_transport': fields.selection([('By air','By Air'),('By sea','By Sea'),('By road','By Road')],'Kind Of Transport'),
            'factory_id': fields.many2one('res.partner','Factory'),
            'loading_code': fields.char('Loading Code',size=256),
            'routing_id': fields.many2one('stock.routing','Routings'),
            'payment_term' : fields.many2one('account.payment.term', 'Payment Term'),
            'incoterm': fields.selection(_incoterm_get, 'Incoterm',size=3),
            'minimum_planned_date':fields.function(_minimum_planned_date, fnct_inv=_set_minimum_planned_date, method=True,store=True, string='Planned Date', type='date', help="This is computed as the minimum scheduled date of all purchase order lines' products."),
              }
    def onchange_routing_id(self, cr, uid, ids, routing_id):
        if routing_id:
            rout_obj=self.pool.get('stock.routing')
            rout_data=rout_obj.read(cr,uid,routing_id,['port_of_loading','kind_transport','segment_sequence_ids'])
            port_load=rout_data['port_of_loading']
            kind_transport=rout_data['kind_transport']
            segment_ids=rout_data['segment_sequence_ids']
            segment_data=self.pool.get('segment.sequence').read(cr,uid,segment_ids,['sequence','port_of_destination'])
            first_seq=segment_data[0]['sequence']
            first_dest=segment_data[0]['port_of_destination']
            i=1
            for i in range(1,len(segment_data)):
                if segment_data[i]['sequence']>first_seq:
                    first_seq=segment_data[i]['sequence']
                    first_dest=segment_data[i]['port_of_destination']
            
            #return {'value':{'location_id': port_load,'port_of_loading': port_load,'kind_transport': kind_transport,'port_of_destination': first_dest}}
            return {'value':{'location_id': port_load,'port_of_loading': port_load,'kind_transport': kind_transport}}
        else:
            return {'value':{'location_id': False,'port_of_loading': False,'kind_transport': False}}
        
    def _get_po_no(self, cr, uid, context={}):
        sequence_pool = self.pool.get('ir.sequence')
        sequence_id = 'purchase.order'
        test = 'code=%s'
        cr.execute('select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where '+test+' and active=True', (sequence_id,))
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return sequence_pool._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + sequence_pool._process(res['suffix'])
            else:
                return sequence_pool._process(res['prefix']) + sequence_pool._process(res['suffix'])
        return False

    _defaults = {
#           'name' : _get_po_no,
            'name' : lambda *a : 'PO/',
            }
    
    def button_rfq(self, cr, uid, ids, context={}):
        for id in ids:
            next_po = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
            self.write(cr, uid, [id], {'state' : 'rfq', 'name':next_po }, context=context)
        return True
    def set_confirm_moves(self, cr, uid, move_ids):
        move_datas = self.pool.get('stock.move').read(cr, uid, move_ids, fields=['move_history_ids'])
        history_ids = [x['move_history_ids'] and x['move_history_ids'][0] or False for x in move_datas]
        history_ids = [x for x in history_ids if x]
        if history_ids:
            self.pool.get('stock.move').write(cr, uid, history_ids, {'state' : 'confirmed'})
            self.set_confirm_moves(cr, uid, history_ids)
            
    def action_picking_create(self, cr, uid, ids, *args):
        picking_id = False
        all_move_ids=[]
        sequence_id=self.pool.get('ir.sequence').search(cr,uid,[('code','=','stock.picking'),('name','=','Packing')])
        new_name = self.pool.get('ir.sequence').get_id(cr, uid, sequence_id[0])
        for order in self.browse(cr, uid, ids):
            loc_id = order.partner_id.property_stock_supplier.id
            istate = 'none'
            if order.invoice_method=='picking' or order.invoice_method=='automatic':
                istate = '2binvoiced'
            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                'name': new_name,
                'origin': order.name + ((order.origin and (':'+order.origin)) or ''),
#               'origin': ((order.origin and (order.origin+':')) or '') + order.name + ((order.origin and (':'+order.origin)) or ''),
                'type': 'in',
                'address_id': order.dest_address_id.id or order.partner_address_id.id,
                'invoice_state': istate,
                'purchase_id': order.id,
                'port_of_departure': loc_id,
                'port_of_arrival': order.routing_id and order.routing_id.port_of_loading.id,
                'kind_transport': order.routing_id and order.routing_id.kind_transport,
                'loading_code': order.loading_code,
                'sequence_id': sequence_id[0]
            })
            for order_line in order.order_line:
                if not order_line.product_id:
                    continue
                if order_line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    if order.routing_id:
                        dest=order.routing_id.port_of_loading.id
                    else:
                        dest = order.location_id.id
                    
                    stock_prod_id=self.pool.get('stock.production.lot').create(cr,uid, {
                       'name': order.name + ((order.origin and (':'+order.origin)) or ''),
                       'product_id':order_line.product_id.id                                                                
                      })
                   
                    stock_move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': 'PO:'+order_line.name,
                        'product_id': order_line.product_id.id,
                        'product_qty': order_line.product_qty,
                        'product_uos_qty': order_line.product_qty,
                        'product_uom': order_line.product_uom.id,
                        'product_uos': order_line.product_uom.id,
                        'date_planned': order_line.date_planned,
                        'location_id': loc_id,
                        'location_dest_id': dest,
                        'picking_id': picking_id,
                        'move_dest_id': order_line.move_dest_id.id,
                        'state': 'assigned',
                        'purchase_line_id': order_line.id,
                        'prodlot_id': stock_prod_id,
                    })
                    all_move_ids.append(stock_move_id)
                    if order_line.move_dest_id:
                        self.pool.get('stock.move').write(cr, uid, [order_line.move_dest_id.id], {'location_id':order.location_id.id})
            
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
           
        purchase_order_line_ids = self.pool.get('purchase.order.line').search(cr, uid ,[('order_id', 'in', ids)])
    
        if purchase_order_line_ids:
            move_line_ids = self.pool.get('stock.move').search(cr, uid, [('purchase_line_id', 'in', purchase_order_line_ids),('state','<>','draft')])
            
            self.pool.get('stock.move').action_confirm(cr, uid, all_move_ids)
            self.pool.get('stock.move').write(cr, uid, all_move_ids, {'state': 'assigned'})
            self.set_confirm_moves(cr, uid, all_move_ids)

        return picking_id
        
purchase_order()

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
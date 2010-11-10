#-*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
##############################################################################

from osv import osv, fields
import netsvc



def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

class c2c_purchase_bom_split(osv.osv):
    
    _inherit = "purchase.order"

    def action_picking_create(self, cr, uid, ids, *args):
        """ Override Purchase Method."""
        res = super(c2c_purchase_bom_split, self).action_picking_create(cr, uid, ids, *args)
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        bom_obj = self.pool.get('mrp.bom')
        picking = picking_obj.browse(cr, uid, res)
                      
        for order in self.browse(cr, uid, ids):
            loc_id = order.partner_id.property_stock_supplier.id

            for order_line in order.order_line:
                if not order_line.product_id:
                    continue
                todo_moves = []
                bom_ids = bom_obj._bom_find(cr, uid, order_line.product_id.id, order_line.product_uom.id, properties=[])
                if bom_ids:
                    bom = bom_obj.browse(cr, uid, [bom_ids])[0]
                    if bom.type == 'phantom':
                        if picking.move_lines:
                            for move in picking.move_lines:
                                move_obj.write(cr, uid, [move.id], {'state': 'draft'})
                                move_obj.unlink(cr, uid, [move.id])   
                        
                        factor = order_line.product_qty * order_line.product_uom.factor / bom.product_uom.factor
                        bom_ids = self.purchase_bom_explode(cr, uid, bom, factor/ bom.product_qty, properties=[])
                        for bom in bom_ids[0]:
                            if order_line.product_id.product_tmpl_id.type in ('product', 'consu'):
                                dest = order.location_id.id
                                move = move_obj.create(cr, uid, {
                                    'name': 'PO:'+bom['name'],
                                    'product_id': bom['product_id'],
                                    'product_qty': bom['product_qty'],
                                    'product_uos_qty': bom['product_qty'],
                                    'product_uom':  bom['product_uom'],
                                    'product_uos': bom['product_uos'],
                                    'date_planned': order_line.date_planned,
                                    'location_id': loc_id,
                                    'location_dest_id': order.location_id.id,
                                    'picking_id': res,
                                    'move_dest_id': order_line.move_dest_id.id,
                                    'state': 'draft',
                                    'purchase_line_id': order_line.id,
                                })
                                todo_moves.append(move)    
            move_obj.action_confirm(cr, uid, todo_moves)
            move_obj.force_assign(cr, uid, todo_moves)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', res, 'button_confirm', cr)

        return res

        
    def purchase_bom_explode(self, cr, uid, bom, factor, properties, addthis=False, level=0):
        factor = factor / (bom.product_efficiency or 1.0)
        factor = rounding(factor, bom.product_rounding)
        if factor<bom.product_rounding:
            factor = bom.product_rounding
        result = []
        result2 = []
        phantom=False
        normal = False
        if bom.type=='phantom' and not bom.bom_lines:
            newbom = self.pool.get('mrp.bom')._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)
            if newbom:
                res = self.purchase_bom_explode(cr, uid, self.browse(cr, uid, [newbom])[0], factor*bom.product_qty, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
                phantom=True
            else:
                phantom=False
        if bom.type == 'normal' and bom.bom_lines:
            result.append(
                {
                    'name': bom.product_id.name,
                    'product_id': bom.product_id.id,
                    'product_qty': bom.product_qty * factor,
                    'product_uom': bom.product_uom.id,
                    'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
                    'product_uos': bom.product_uos and bom.product_uos.id or False,
                })
            phantom = True
        
        if not phantom:
            if addthis and not bom.bom_lines:
                result.append(
                {
                    'name': bom.product_id.name,
                    'product_id': bom.product_id.id,
                    'product_qty': bom.product_qty * factor,
                    'product_uom': bom.product_uom.id,
                    'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
                    'product_uos': bom.product_uos and bom.product_uos.id or False,
                })
                
            if bom.routing_id:
                for wc_use in bom.routing_id.workcenter_lines:
                    wc = wc_use.workcenter_id
                    d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                    mult = (d + (m and 1.0 or 0.0))
                    cycle = mult * wc_use.cycle_nbr
                    result2.append({
                        'name': bom.routing_id.name,
                        'workcenter_id': wc.id,
                        'sequence': level+(wc_use.sequence or 0),
                        'cycle': cycle,
                        'hour': float(wc_use.hour_nbr*mult + (wc.time_start+wc.time_stop+cycle*wc.time_cycle) * (wc.time_efficiency or 1.0)),
                    })

            for bom2 in bom.bom_lines:
                    res = self.purchase_bom_explode(cr, uid, bom2, factor, properties, addthis=True, level=level+10)
                    result = result + res[0]
                    result2 = result2 + res[1]
        return result, result2

        
        
c2c_purchase_bom_split()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

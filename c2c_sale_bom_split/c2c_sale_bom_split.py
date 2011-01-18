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

class c2c_sale_bom_split(osv.osv):
    
    _inherit = "sale.order"

    def action_ship_create(self, cr, uid, ids, *args):
        picking_id = False
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        for order in self.browse(cr, uid, ids, context={}):
            output_id = order.shop_id.warehouse_id.lot_output_id.id
            picking_id = False
            for line in order.order_line:
                proc_id = False
                date_planned = DateTime.now() + DateTime.DateTimeDeltaFromDays(line.delay or 0.0)
                date_planned = (date_planned - DateTime.DateTimeDeltaFromDays(company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
                if line.state == 'done':
                    continue
                if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    location_id = order.shop_id.warehouse_id.lot_stock_id.id
                    if not picking_id:
                        loc_dest_id = order.partner_id.property_stock_customer.id
                        picking_id = self.pool.get('stock.picking').create(cr, uid, {
                            'origin': order.name,
                            'type': 'out',
                            'state': 'auto',
                            'move_type': order.picking_policy,
                            'sale_id': order.id,
                            'address_id': order.partner_shipping_id.id,
                            'note': order.note,
                            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',

                        })

                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': line.name[:64],
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'date_planned': date_planned,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos_qty,
                        'product_uos': (line.product_uos and line.product_uos.id)\
                                or line.product_uom.id,
                        'product_packaging': line.product_packaging.id,
                        'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
                        'location_id': location_id,
                        'location_dest_id': output_id,
                        'sale_line_id': line.id,
                        'tracking_id': False,
                        'state': 'draft',
                        #'state': 'waiting',
                        'note': line.notes,
                    })
                    proc_id = self.pool.get('mrp.procurement').create(cr, uid, {
                        'name': order.name,
                        'origin': order.name,
                        'date_planned': date_planned,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                                or line.product_uom_qty,
                        'product_uos': (line.product_uos and line.product_uos.id)\
                                or line.product_uom.id,
                        'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                        'procure_method': line.type,
                        'move_id': move_id,
                        'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                    })
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
                    self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                elif line.product_id and line.product_id.product_tmpl_id.type == 'service':
                    proc_id = self.pool.get('mrp.procurement').create(cr, uid, {
                        'name': line.name,
                        'origin': order.name,
                        'date_planned': date_planned,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                        'procure_method': line.type,
                        'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                    })
                    self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
                else:
                    #
                    # No procurement because no product in the sale.order.line.
                    #
                    pass

            val = {}
            if picking_id:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)

            if order.state == 'shipping_except':
                val['state'] = 'progress'

                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
            self.write(cr, uid, [order.id], val)

        return True

    def action_ship_create(self, cr, uid, ids, *args):
        """ Override sale picking creation Method."""
        res = super(c2c_sale_bom_split, self).action_ship_create(cr, uid, ids, *args)
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        bom_obj = self.pool.get('mrp.bom')
                      
        for order in self.browse(cr, uid, ids):
            # Take all related picking that are available
            picking_ids = picking_obj.search(cr,uid,[('sale_id','=',order.id),('state','not in',['cancel','done'])])
            if not picking_ids:
                continue
            if type(picking_ids) != list:
                picking_ids = [picking_ids]
            picking = picking_obj.browse(cr, uid, picking_ids)[0]
            todo_moves = []
            for line in picking.move_lines:
                
                bom_ids = bom_obj._bom_find(cr, uid, line.product_id.id, line.product_uom.id, properties=[])
                if bom_ids:
                    bom = bom_obj.browse(cr, uid, [bom_ids])[0]
                    if bom.type == 'phantom':

                        move_obj.write(cr, uid, [line.id], {'state': 'draft'})
                        move_obj.unlink(cr, uid, [line.id])
                        
                        factor = line.product_qty * line.product_uom.factor / bom.product_uom.factor
                        bom_ids = self.sale_bom_explode(cr, uid, bom, factor/ bom.product_qty, properties=[])
                        for bom in bom_ids[0]:
                            if line.product_id.product_tmpl_id.type in ('product', 'consu'):
                                move = move_obj.create(cr, uid, {
                                    'name': 'SO:'+bom['name'],
                                    'product_id': bom['product_id'],
                                    'product_qty': bom['product_qty'],
                                    'product_uos_qty': bom['product_qty'],
                                    'product_uom':  bom['product_uom'],
                                    'product_uos': bom['product_uos'],
                                    'date_planned': line.date_planned,
                                    'location_id': line.location_id.id,
                                    'location_dest_id': line.location_dest_id.id,
                                    'picking_id': picking.id,
                                    'move_dest_id': line.move_dest_id.id,
                                    'state': 'draft',
                                    'sale_line_id': line.sale_line_id.id,
                                })
                                todo_moves.append(move)   
            
            move_obj.action_confirm(cr, uid, todo_moves)
            move_obj.action_assign(cr, uid, todo_moves)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_confirm', cr)

        return res

        
    def sale_bom_explode(self, cr, uid, bom, factor, properties, addthis=False, level=0):
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
                res = self.sale_bom_explode(cr, uid, self.browse(cr, uid, [newbom])[0], factor*bom.product_qty, properties, addthis=True, level=level+10)
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
                    res = self.sale_bom_explode(cr, uid, bom2, factor, properties, addthis=True, level=level+10)
                    result = result + res[0]
                    result2 = result2 + res[1]
        return result, result2

        
        
c2c_sale_bom_split()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

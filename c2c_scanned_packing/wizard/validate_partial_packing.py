 # -*- encoding: utf-8 -*-
 ##############################################################################
 #
 #    Copyright Camptocamp SA
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
from tools.translate import _
import netsvc

class validate_partial_packing(osv.osv_memory):
    
    """Confirmation msg before Validating Partial Picking"""
    
    _name = 'validate.partial.packing'
    _description = __doc__
    
    def make_partial(self, cr, uid, ids, context=None):
        pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        picking = pick_obj.browse(cr, uid, context.get('record_id'))
        move_ids = move_obj.search(cr, uid, [('picking_id','=', picking.id)])
        ir_obj = self.pool.get('ir.sequence')
        new_picking = None
        new_moves = []
        complete, too_many, too_few = [], [], []        
        for move in move_obj.browse(cr, uid, move_ids):
            
            if move.product_qty ==move.scan_qty:
                complete.append(move)
            elif move.product_qty > move.scan_qty:
                too_few.append(move)
            else:
                too_many.append(move)
        for move in too_few:                    
            if not new_picking:
                new_picking = pick_obj.copy(cr, uid, picking.id,
                        {
                            'name': ir_obj.get(cr, uid, 'stock.picking'),
                            'move_lines' : [],
                            'state':'draft',
                        })
            if move.scan_qty <> 0:
                new_obj = move_obj.copy(cr, uid, move.id,
                    {
                        'product_qty' : move.scan_qty,
                        'product_uos_qty':move.scan_qty,
                        'picking_id' : new_picking,
                        'state': 'assigned',
                        'move_dest_id': False,
                        'price_unit': move.price_unit,
                    })
            move_obj.write(cr, uid, [move.id],
                    {
                        'product_qty' : move.product_qty - move.scan_qty,
                        'product_uos_qty':move.product_qty - move.scan_qty,
                    })
            
        if new_picking:
            move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in too_many:
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty' : move.scan_qty,
                            'product_uos_qty': move.scan_qty,
                            'picking_id': new_picking,
                        })
        else:
            for move in too_many:
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty': move.scan_qty,
                            'product_uos_qty': move.scan_qty
                        })
            
        wf_service = netsvc.LocalService("workflow")
        if new_picking:
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        # Then we finish the good picking
        if new_picking:
            pick_obj.write(cr, uid, [picking.id], {'backorder_id': new_picking})
            pick_obj.action_move(cr, uid, [new_picking])
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
            wf_service.trg_write(uid, 'stock.picking', picking.id, cr)
        else:
            pick_obj.action_move(cr, uid, [picking.id])
            wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_done', cr)
        bo_name = ''
        if new_picking:
            bo_name = pick_obj.read(cr, uid, [new_picking], ['name'])[0]['name']
        for move in  move_obj.browse(cr, uid, move_ids):    
            move_obj.write(cr, uid, [move.id], {'scan_qty': 0.0})
        
        return {'new_picking':new_picking or False, 'back_order':bo_name}

validate_partial_packing()

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
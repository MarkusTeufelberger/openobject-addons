# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure S.L.
#                     (http://www.nan-tic.com) All Rights Reserved.
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

import netsvc
from osv import fields,osv
from tools.translate import _
import sys
import tempfile
import os

class stock_scanner_config(osv.osv):
    _name = 'stock.scanner.config'

    _columns = {
        'name':fields.char( 'Name', size=30 ),
        'active':fields.boolean( 'Active' ),
        'default':fields.boolean('Default'),
        'auto_create_lot': fields.boolean('Create automatic lot on input material',help ='Create atutomatic lot on input material, taking care of supplier ref, dluo...' ),
        'fill_quantity': fields.boolean('Fill Qty:', help='Mark pending quantity must be loaded when product is scanned' ),
        'input_reports_ids': fields.many2many( 'ir.actions.report.xml', 'scanner_input_repors_rel', 'warehouse_id','report_id' , 'Input Reports' , help='Reports to print after input packing has done' ),
        'output_reports_ids': fields.many2many( 'ir.actions.report.xml', 'scanner_output_reports_rel', 'warehouse_id','report_id', 'Output Reports', help='Reports to print after output packing has done' ),
    }

    
    _defaults = {
        'active': lambda *a: True,
    }
    
    def write(self, cr, uid, ids, vals, context=None):

        if context is None:
            context={}

        if 'default' in vals.keys() and vals.get('default'):
            config_ids = self.search(cr, uid, [], context=context)
            self.write( cr, uid, config_ids, {'default':False}, context=context)

        return super( stock_scanner_config, self).write(cr, uid, ids,vals, context)

stock_scanner_config()

 
class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def onchange_scanned_ean(self, cr, uid, ids, product_id, ean13, context):
        if not ids or not (product_id and ean13) :
            return { 'value':{},'warning':{'title':'Ean13 Code will be updated', 'message':'Please select product First'} }
        product = self.pool.get('product.product').browse(cr,uid, product_id , context=context )

        if ean13 and len(ean13) ==  13:
            return {'value':{},'warning': { 'title':'Ean13 Code Wil be updated',
                                           'message':'The number %s will be updated to product %s  \n Current Ean13 : %s'%(ean13,product.product_tmpl and product.product_tmpl_id.name or '',product.ean13 or '') } }
        elif ean13 and len(ean13) != 13:
            return {'value':{},'warning': { 'title':'Ean13 Code Wil be updated',
                                           'message':'The number %s is not correct'%(ean13) } }
 
 
        return {}

    def on_change_scanned_product(self, cr, uid, ids, product_id, scanned_quantity, context):

        if not ids or not product_id:
            return {}

        picking = self.browse(cr, uid, ids[0], context)

        config=False
        config_id = self.pool.get('stock.scanner.config').search(cr, uid, [('default','=',True)],context=context)
        if config_id:
            config = self.pool.get('stock.scanner.config').browse(cr,uid, config_id[0], context=context)


        result={'value':{}}
        for move in picking.pending_move_line_ids:
            if move.product_id.id == product_id:
                product = self.pool.get('product.product').browse(cr, uid, product_id, context)
                if len(product.packaging) == 1:
                    result['value']['scanned_packaging_id'] = product.packaging[0].id
                if config and config.fill_quantity:
                    result['value']['scanned_quantity'] = move.pending_quantity
                elif scanned_quantity == 0:
                    result['value']['scanned_quantity'] = 1

                if picking.scanned_ean:
                    result['warning'] = {'title':'Ean13 Code Will be Updated','message':'Ean13 %s will be updated on product %s with current Ean13 %s'%(picking.scanned_ean,move.product_id.product_tmpl_id.name,move.product_id.ean13 or '' )}

                return result
        return { 'warning': {
                'title': _('Product Error'),
                'message': _('This product is not pending to be scanned in this order.'),
            }
        }

    def _pending_move_line_ids(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for picking in self.browse(cr, uid, ids, context):
            lines = []
            for line in picking.move_lines:
                if line.product_qty - line.received_quantity > 0:
                    lines.append( line.id )
            result[picking.id] = lines
        return result


    def _get_scanned_move(self,  cr, uid, move_lines, product_id, lot_ref, context ):
        """ Get possible scanned move """
        moves =  []
        for m in move_lines:
            if m.product_id.id == product_id:
              if m.prodlot_id and m.prodlot_id.id or False:
                if m.prodlot_id.ref == lot_ref:
                  moves.insert( 0, m )
                  continue
              moves.append( m )
        return moves


    def _scanned_product(self, cr, uid, ids, context):        
        move_ids = []
        for picking in self.browse(cr, uid, ids, context):
            if not picking.scanned_product_id:
                continue
            if picking.scanned_quantity <= 0:
                continue
            product_id = picking.scanned_product_id.id
            pending_quantity = picking.scanned_quantity
            lot_ref = picking.scanned_lot_ref
            packing_id =  picking.scanned_packaging_id
            scanned_dluo = picking.scanned_dluo

            default_create_lot=False
            if picking.type == 'in':
                config_ids = self.pool.get('stock.scanner.config').search(cr,uid,[], context=context)
                if config_ids:
                    config = self.pool.get('stock.scanner.config').browse(cr,uid,config_ids[0],context=context )
                    print "config:",config
                    default_create_lot = config.auto_create_lot or False
                

            moves=self._get_scanned_move( cr,  uid,  picking.move_lines,  product_id,  lot_ref , context)
            print "moves...",moves
            for move in moves:
                create_lot=default_create_lot #Mark if its necessary to create lot.
                qty = min(pending_quantity, move.pending_quantity)
                print "qty"
                if qty == 0:
                    continue
                if  picking.type == 'in' and move.prodlot_id and move.prodlot_id.id or False:
                    if move.prodlot_id.ref == lot_ref or lot_ref == False:
                        create_lot=False
                        lot_id=move.prodlot_id.id
                    else:
                        move_copy_id = self.pool.get('stock.move').copy(cr, uid, move.id, {
                            'product_qty' : move.pending_quantity,
                            'received_quantity': None,
                            'state':move.state,
                            'prodlot_id': None,
                            })

                        self.pool.get('stock.move').write(cr, uid, [move.id], {
                                                'product_qty':move.received_quantity,
                                                'received_quantity': move.received_quantity,
                                        }, context)
                        move=None
                        move = self.pool.get('stock.move').browse(cr, uid, move_copy_id)

                lot_id = False
                if create_lot:
                    ctx = context.copy()
                    data ={}
                    data['ref'] = lot_ref
                    data['product_id'] = product_id
                    if not  scanned_dluo:
                        ctx['product_id'] = move.product_id.id
                    else:
                        data['dluo']=scanned_dluo
                    
                    lot_id = self.pool.get('stock.production.lot').create(cr, uid, data,ctx)

                
                if picking.type =="out":
                    lot_id = move.prodlot_id.id

                self.pool.get('stock.move').write(cr, uid, [move.id], {
                        'received_quantity': move.received_quantity + qty,
                        'prodlot_id': lot_id,
                        'product_packaging': packing_id.id,
                }, context)

                move_ids.append( move.id )
                pending_quantity -= qty
                if pending_quantity <= 0:
                    break


            if pending_quantity:
                if pending_quantity == picking.scanned_quantity:
                    raise osv.except_osv(_('Product Error'), _('There are no pending moves with this product.'))
                else:
                    raise osv.except_osv(_('Product Error'),
                        _('Wrong product quantity. Expected %(expected).2f at most but you introduced %(introduced).2f.') % {
                            'expected': picking.scanned_quantity - pending_quantity,
                            'introduced': picking.scanned_quantity,
                        })

        self.pool.get('stock.picking').write(cr, uid, ids, {
            'scanned_product_id': False,
            'scanned_quantity': 0,
            'scanned_lot_ref': False,
            'scanned_packaging_id': False,
            'scanned_dluo': False,
            'scanned_ean':False,
        }, context)
        return move_ids

    def action_scanned(self, cr, uid, ids, context=None):
        pick = self.browse( cr, uid, ids , context=context)[0]
        print  "product:",pick.scanned_product_id.id, 

        scanned_product = pick.scanned_product_id.id
        scanned_ean = pick.scanned_ean
        if pick.scanned_product_id or pick.scanned_quantity:
           # Call _scanned_product if either one of the two fields are updated because
           # the function will reset their values to NULL
           print "hoollllaaa"
           self._scanned_product(cr, uid, ids, context)

        if scanned_ean and len(scanned_ean) ==  13:
            self.pool.get('product.product').write( cr, uid,scanned_product, {'ean13':scanned_ean} ,context=context)
        

        return False

    _columns = {
        'pending_move_line_ids': fields.function(_pending_move_line_ids, method=True, type='one2many', relation='stock.move', string='Pending Lines', store=False, help='List of pending products to be received.'),
        'scanned_product_id': fields.many2one('product.product', 'Scanned product', states={'assigned': [('readonly', False)], 'confirmed':[('readonly',False)]}, readonly=True, help='Scan the code of the next product.'),
        'scanned_quantity': fields.float('Quantity', states={'assigned': [('readonly', False)],'confirmed':[('readonly',False)]}, readonly=True, help='Quantity of the scanned product.'),
        'scanned_lot_ref': fields.char('Supplier Lot Ref.', size=64, states={'assigned': [('readonly', False)]}, readonly=True, help="Supplier's lot reference."),
        'scanned_packaging_id': fields.many2one('product.packaging', 'Packaging', states={'assigned': [('readonly', False)]}, readonly=True, help="Product's packaging."),
        'scanned_dluo': fields.date('DLUO', states={'assigned': [('readonly', False)]}, readonly=True, help="Lot's expire date."),
        'scanned_ean': fields.char('Ean13',size=13,help='Type ean for update on  current product'),
    }



    def print_report(self, cr, uid, ids, report_ids,context):
        data = {
                'ids': ids,
                'model': 'stock.picking',
        }
        print "print report"
        for report in self.pool.get('ir.actions.report.xml').browse( cr, uid, report_ids , context):
            data['name'] = "report.%s"%report.report_name
            printer = report.behaviour()[report.id]['printer']
            if not printer:
                raise osv.except_osv(_('Invalid printer'), _('No printer specified for report "%s".') % report.name)
       
            try:
                r  = netsvc.LocalService('report.%s' % report.report_name)
                result, format = r.create(cr, uid,ids, data, context)
            except:
                raise osv.except_osv( _('Invalid Report'), _('Failed to print specified report %s'%report.name ))
            
            try:
                fd, file_name = tempfile.mkstemp()  
                os.write(fd, result)
            finally:
                os.close(fd)
                os.system( "lpr -P %s %s" % (printer, file_name) )





    def action_force_scanner_confirm(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context):
            for move in picking.move_lines:
                data={'received_quantity':move.product_qty }
                self.pool.get('stock.move').write( cr, uid, [move.id], data, context=context) 
        return self.action_scanner_confirm( cr, uid, ids, context )

    def action_scanner_confirm(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context):
            new_picking = None
            new_moves = []

            complete, too_many, too_few , none = [], [], [],[]
            for move in picking.move_lines:
                if move.received_quantity == None or move.received_quantity == False or move.received_quantity == 0:
                    none.append( move )
                elif move.product_qty == move.received_quantity:
                    complete.append(move)
                elif move.product_qty > move.received_quantity:
                    too_few.append(move)
                else:
                    too_many.append(move)

                if len( none) == len( picking.move_lines):
                    return {'new_picking': False}

                # Average price computation
                if (picking.type == 'in') and (move.product_id.cost_method == 'average'):
                    currency_obj = self.pool.get('res.currency')
                    uom_obj = self.pool.get('product.uom')

                    product = self.pool.get('product.product').browse(cr, uid, move.product_id.id, context)
                    user = self.pool.get('res.users').browse(cr, uid, uid, context)

                    qty = move.received_quantity
                    qty = self.pool.get('product.uom')._compute_qty(cr, uid, uom, qty, product.uom_id.id)

                    if (qty > 0):
                        new_price = self.pool.get('res.currency').compute(cr, uid, currency,
                                user.company_id.currency_id.id, price)
                        new_price = self.pool.get('product.uom')._compute_price(cr, uid, uom, new_price,
                                product.uom_id.id)
                        if product.qty_available<=0:
                            new_std_price = new_price
                        else:
                            new_std_price = ((product.standard_price * product.qty_available)\
                                + (new_price * qty))/(product.qty_available + qty)

                        self.pool.get('product.product').write(cr, uid, [product.id], {
                            'standard_price': new_std_price
                        }, context)
                        self.pool.get('stock.move').write(cr, uid, [move.id], {
                            'price_unit': new_price
                        }, context)

            if len(too_many) >0 or len(too_few) > 0 or len(none) > 0:
                new_picking = self.copy(cr, uid, picking.id, {
                    'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking'),
                    'move_lines' : [],
                    'state':'draft',
                    }, context)
 
            for move in too_few:
                if move.received_quantity <> 0:
                    new_obj = self.pool.get('stock.move').copy(cr, uid, move.id, {
                        'product_qty' : move.received_quantity,
                        'product_uos_qty': move.received_quantity,
                        'picking_id' : new_picking,
                        'state': 'assigned',
                        'move_dest_id': False,
                        'price_unit': move.price_unit,

                    }, context)
                self.pool.get('stock.move').write(cr, uid, [move.id], {
                    'product_qty' : move.product_qty - move.received_quantity,
                    'product_uos_qty':move.product_qty - move.received_quantity,
                    'prodlot_id': None,
                    'received_quantity':0,
                }, context)

            if new_picking:
                print "NEW PICKING"
                self.pool.get('stock.move').write(cr, uid, [c.id for c in complete], {'picking_id': new_picking}, context)
                for move in too_many:
                    self.pool.get('stock.move').write(cr, uid, [move.id], {
                        'product_qty' : received_quantity,
                        'product_uos_qty': received_quantity,
                        'picking_id': new_picking,
                    }, context)
            else:
                for move in too_many:
                    self.pool.get('stock.move').write(cr, uid, [move.id], {
                        'product_qty': received_quantity,
                        'product_uos_qty': received_quantity,
                        'prodlot_id':False,
                    }, context)

            # At first we confirm the new picking (if necessary)
            wf_service = netsvc.LocalService("workflow")
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)

            # Then we finish the good picking
            if new_picking:
                self.write(cr, uid, [picking.id], {'backorder_id': new_picking}, context)
                self.action_move(cr, uid, [new_picking], context)
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', picking.id, cr)
            else:
                self.action_move(cr, uid, [picking.id], context)
                wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_done', cr)

            #print Reports.
            reports_ids =[]
            config_ids = self.pool.get('stock.scanner.config').search(cr,uid,[('default','=',True)], context=context)
            if config_ids:
                config = self.pool.get('stock.scanner.config').browse(cr,uid,config_ids[0],context=context )
                if picking.type == "in":
                    reports_ids = [x.id for x in config.input_reports_ids]
                elif picking.type == "out":
                    reports_ids = [x.id for x in config.output_reports_ids]

            if len( reports_ids ) >= 1:
                self.print_report( cr, uid, [picking.id], reports_ids, context )

            cr.commit()
        return {'new_picking':new_picking or False}

stock_picking()


class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _pending_quantity(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for move in self.browse(cr, uid, ids, context):
            result[move.id] = move.product_qty - move.received_quantity
        return result

    _columns = {
        'received_quantity': fields.float('Received Quantity', help='Quantity of product received'),
        'pending_quantity': fields.function(_pending_quantity, method=True, type='float', string='Pending Quantity', store=False, help='Quantity pending to be received'),
    }

stock_move()


class product_product(osv.osv):
    _inherit = 'product.product'

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        result = super(product_product,self).name_search(cr, user, name, args, operator, context, limit)
        if name and not result:
            info_ids = self.pool.get('product.supplierinfo').search(cr, user, [('product_barcode',operator,name)], context=context, limit=limit)
            ids = []
            for info in self.pool.get('product.supplierinfo').browse(cr, user, info_ids, context):
                ids.append( info.product_id.id )
            result += self.name_get(cr, user, ids, context)
        return result
product_product()

class product_supplierinfo(osv.osv):
    _inherit = 'product.supplierinfo'
    _columns = {
        'product_barcode': fields.char('Product Barcode', size=30, help='The barcode for this product of this supplier.'),
    }
product_supplierinfo()

class nan_stock_picking_scanner_confirm_wizard(osv.osv_memory):
    _name = 'nan.stock.picking.scanner.confirm.wizard'

    def action_force_scanner_confirm( self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').action_force_scanner_confirm( cr, uid, [context['active_id']],context)

    def action_scanner_confirm(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').action_scanner_confirm(cr, uid, [context['active_id']], context)
nan_stock_picking_scanner_confirm_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


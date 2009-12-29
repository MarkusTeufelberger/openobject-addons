# -*- encoding: utf-8 -*-
#########################################################################
#This module intergrates Open ERP with the magento core                 #
#Core settings are stored here                                          #
#########################################################################
#                                                                       #
# Copyright (C) 2009  Raphaël Valyi                                     #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields, osv
import tools
import ir
import pooler
from mx import DateTime

class crm_case(osv.osv):
    _inherit = "crm.case"
    _columns = {
        'rma_ref': fields.char('Incident Ref', size=64, required=True, select=1),
        'incoming_picking_id': fields.many2one('stock.picking', 'Incoming Picking', required=False, select=1),
        'outgoing_picking_id': fields.many2one('stock.picking', 'Outgoing Picking', required=False, select=True),
        'related_incoming_picking_state': fields.related('incoming_picking_id', 'state', type="char", string="Related Picking State", readonly=True),
        'related_outgoing_picking_state': fields.related('outgoing_picking_id', 'state', type="char", string="Related Picking State", readonly=True),
        'in_supplier_picking_id': fields.many2one('stock.picking', 'Return To Supplier Picking', required=False, select=True),
        'out_supplier_picking_id': fields.many2one('stock.picking', 'Return From Supplier Picking', required=False, select=True),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial / Lot Number'),
        'product_id': fields.many2one('product.product', 'Product'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice')
    }
    
    _defaults = {
        'rma_ref': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'rma'),
    }


    def onchange_form(self, cr, uid, ids, partner_id=False, invoice_id=False, product_id=False, prodlot_id=False):
        
        def inv_2_product(cr, uid, invoice_id):
            product_ids = []
            inv_lines = self.pool.get('account.invoice').browse(cr, uid, invoice_id).invoice_line
            
            for inv_line in inv_lines:
                if not self.pool.get('account.invoice.line').read(cr, uid, inv_line.id)['product_id']:
                    continue
                product_ids.append(self.pool.get('account.invoice.line').read(cr, uid, inv_line.id)['product_id'][0])

            return product_ids
        
        
        def inv_2_prodlot(cr, uid, invoice_id):
            stock_move_ids = []
            prodlot_ids = []
            sale_line_ids = []
            inv_lines = self.pool.get('account.invoice').browse(cr, uid, invoice_id).invoice_line  
                
            for inv_line in inv_lines:  
                cr.execute("select order_line_id from sale_order_line_invoice_rel where invoice_id= %s" % int(inv_line.id))
                sale_line_ids = cr.fetchone()
                stock_move_ids.append(self.pool.get('stock.move').search(cr, uid, [('sale_line_id', 'in', sale_line_ids)])[0])

                for stock_move_id in stock_move_ids:
                    if not self.pool.get('stock.move').read(cr, uid, stock_move_id)['prodlot_id']:
                        continue
                    prodlot_ids.append(self.pool.get('stock.move').read(cr, uid, stock_move_id)['prodlot_id'][0])
                    
            return prodlot_ids
        
             
        
        
        result = {}
        
        print 'partner_id, invoice_id, product_id, prodlot_id', partner_id, invoice_id, product_id, prodlot_id
        
        if not partner_id and not invoice_id:
            print 'pass'
            result = {}
        
        elif not invoice_id:
            print 'partner'           
            result = {'value':{'invoice_id': False, 'product_id': False, 'prodlot_id': False}, 'domain':{'invoice_id':"[('partner_id','=',partner_id)]"}}

        else:
            print 'else'
            product_ids = inv_2_product(cr, uid, invoice_id)
            prodlot_ids = inv_2_prodlot(cr, uid, invoice_id)
            result = {'domain':{'product_id':"[('id','in', %s)]" % product_ids, 'prodlot_id':"[('id','in', %s)]" % prodlot_ids}}   

        return result

#'value':{'partner_id': self.pool.get('account.invoice').browse(cr, uid, invoice_id).id, 'product_id':False, 'prodlot_id': False}, 
    
    
    








crm_case()
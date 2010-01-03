# -*- encoding: utf-8 -*-
#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2009  Raphaël Valyi, Sébastien Beau                     #
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

    global parent
    parent = {}

    def onchange_form(self, cr, uid, ids, action, partner_id=False, invoice_id=False, product_id=False, prodlot_id=False):
        
        def invoice_2_product(cr, uid, invoice_ids):
            inv_lines_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', invoice_ids)])
            res = self.pool.get('account.invoice.line').read(cr, uid, inv_lines_ids,['product_id'])
            return set([x['product_id'][0] for x in res if x['product_id']])
        
        
        def invoice_2_prodlot(cr, uid, invoice_ids):
            sale_line_ids = []
            inv_line_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', invoice_ids)])
            if not inv_line_ids:
                return []                
            cr.execute("select order_line_id from sale_order_line_invoice_rel where invoice_id in ("+ ','.join(map(lambda x: str(x),inv_line_ids))+')')
            res = cr.fetchall()
            for i in res:
                for j in i:
                    sale_line_ids.append(j)
            stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', 'in', sale_line_ids)])
            res = self.pool.get('stock.move').read(cr, uid, stock_move_ids, ['prodlot_id'])
            return set([x['prodlot_id'] for x in res if x['prodlot_id']])
        
        def prodlot_2_product(cr, uid, prodlot_ids):          
            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)])
            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids, ['product_id'])
            return set([x['product_id'][0] for x in res if x['product_id']])
        
        
        def product_2_prodlot(cr, uid, product_ids):
            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)])
            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids, ['prodlot_id'])
            return set([x['prodlot_id'] for x in res if x['prodlot_id']])
            
            
        def stock_move_2_invoice(cr, uid, stock_move_ids):
            inv_line_ids = []
            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids, ['sale_line_id'])
            sale_line_ids = [x['sale_line_id'][0] for x in res if x['sale_line_id']]
            if not sale_line_ids:
                return []
            cr.execute("select invoice_id from sale_order_line_invoice_rel where order_line_id in ("+ ','.join(map(lambda x: str(x),sale_line_ids))+')')
            res = cr.fetchall()     
            for i in res:
                for j in i:
                    inv_line_ids.append(j)
                    
            res=self.pool.get('account.invoice.line').read(cr, uid, inv_line_ids,['invoice_id'])
            return [x['invoice_id'][0] for x in res if x['invoice_id']]
         
        
        def prodlot_2_invoice(cr, uid, prodlot_ids):

            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)])
            return set(stock_move_2_invoice(cr, uid, stock_move_ids))
        

        def product_2_invoice(cr, uid, product_ids):
            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)])
            return set(stock_move_2_invoice(cr, uid, stock_move_ids))
        
        
        def invoice_2_partner(cr, uid, invoice_ids):
            res=self.pool.get('account.invoice').read(cr, uid, invoice_ids)
            return set([x['partner_id'][0] for x in res if x['partner_id']])
         
        def partner_2_invoice(cr, uid, partner_ids):
            return set(self.pool.get('account.invoice').search(cr, uid, [('partner_id', 'in', partner_ids)]))
            
        
        
        #creates the dictionary for each user
        if not partner_id and not invoice_id and not product_id and not prodlot_id:
            parent[uid]={'partner' : {}, 'invoice' : {}, 'product' : {}, 'prodlot':{}}
            return
        
        filter = {'value':{}, 'domain':{}}
        product_ids=set([])
        prodlot_ids=set([])
        invoice_ids =set([])
        partner_ids =set([])

        #removes fields which have for parent the field which launch the on change
        if parent[uid]['partner'].get(action, False):
            partner_id = False
        if parent[uid]['invoice'].get(action, False):
            invoice_id = False
        if parent[uid]['product'].get(action, False):
            product_id = False
        if parent[uid]['prodlot'].get(action, False):
            prodlot_id = False


        # starts to find all of ids in function of the existing field
        if partner_id:
            if not invoice_id:
                invoice_ids = partner_2_invoice(cr, uid, [partner_id])
                
        if invoice_id:
            if not partner_id:
                partner_ids = invoice_2_partner(cr, uid, [invoice_id])
            if not product_id:
                product_ids = invoice_2_product(cr, uid, [invoice_id])
            if not prodlot_id:
                prodlot_ids = invoice_2_prodlot(cr, uid, [invoice_id])  
        
        if prodlot_id:
            if not product_id:
                if product_ids:
                    product_ids = product_ids.intersection(prodlot_2_product(cr, uid, [prodlot_id]))
                else:
                    product_ids = prodlot_2_product(cr, uid, [prodlot_id])
                    
            if not invoice_id:
                if invoice_ids:
                    invoice_ids = invoice_ids.intersection(prodlot_2_invoice(cr, uid, [prodlot_id]))
                else:
                    invoice_ids = prodlot_2_invoice(cr, uid, [prodlot_id])
            
        if product_id:
            if not prodlot_id:
                if prodlot_ids:
                    prodlot_ids = prodlot_ids.intersection(product_2_prodlot(cr, uid, [product_id]))
                else:
                    prodlot_ids = product_2_prodlot(cr, uid, [product_id])
                    
            if not invoice_id:
                if invoice_ids:
                    invoice_ids = invoice_ids.intersection(product_2_invoice(cr, uid, [product_id]))
                else:
                    invoice_ids = product_2_invoice(cr, uid, [product_id])
        
        invoice_ids = [i for i in invoice_ids]
        if invoice_ids:
            if not partner_id:
                partner_ids = invoice_2_partner(cr, uid, invoice_ids)
                
            if not product_id:
                if product_ids:
                    product_ids = product_ids.intersection(invoice_2_product(cr, uid, invoice_ids))
                else:
                    product_ids = invoice_2_product(cr, uid, invoice_ids)
                    
            if not prodlot_id:
                if prodlot_ids:
                    prodlot_ids = prodlot_ids.intersection(invoice_2_prodlot(cr, uid, invoice_ids))
                else:
                    prodlot_ids = invoice_2_prodlot(cr, uid, invoice_ids)
                    
        
        partner_ids = [i for i in partner_ids]
        product_ids = [i for i in product_ids]
        prodlot_ids = [i for i in prodlot_ids]


        #result are transformed in domain and value filter
        if not partner_id:
            parent[uid]['partner'] = {'invoice' : invoice_id, 'product' : product_id, 'prodlot' : prodlot_id}
            filter['domain']['partner_id']= "[('id','in', %s)]" % partner_ids
            if len(partner_ids)==1:
                filter['value']['partner_id'] = partner_ids[0]
            else:
                filter['value']['partner_id'] = False
            
        if not invoice_id:
            parent[uid]['invoice'] = {'partner' : partner_id, 'product' : product_id, 'prodlot' : prodlot_id}
            filter['domain']['invoice_id']= "[('id','in', %s)]" % invoice_ids
            if len(invoice_ids)==1:
                filter['value']['invoice_id'] = invoice_ids[0]
            else:
                filter['value']['invoice_id'] = False

        if not product_id:
            parent[uid]['product'] = {'partner' : partner_id, 'invoice' : invoice_id, 'prodlot' : prodlot_id}
            filter['domain']['product_id']= "[('id','in', %s)]" % product_ids
            if len(product_ids)==1:
                filter['value']['product_id'] = product_ids[0]
            else:
                filter['value']['product_id'] = False
                
        if not prodlot_id:
            parent[uid]['prodlot'] = {'partner' : partner_id, 'invoice' : invoice_id, 'product' : product_id}
            filter['domain']['prodlot_id']= "[('id','in', %s)]" % prodlot_ids
            if len(prodlot_ids)==1:
                filter['value']['prodlot_id'] = prodlot_ids[0]
            else:
                filter['value']['prodlot_id'] = False

        return filter

crm_case()
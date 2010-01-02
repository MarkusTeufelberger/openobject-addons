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

    global filtre
    filtre = {'value':{}, 'domain':{}}

    global parent
    parent = {'partner' : {}, 'invoice' : {}, 'product' : {}, 'prodlot':{}}

    def onchange_form(self, cr, uid, ids, partner_id=False, invoice_id=False, product_id=False, prodlot_id=False):
        #si on n'utilise pas la nouvelle fonction search ne pas oublier de check avec des if avant d'appeler le read
        
        def invoice_2_product(cr, uid, invoice_ids):
#            product_ids = []
#            inv_lines_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', invoice_ids)])
#            res = self.pool.get('account.invoice.line').read(cr, uid, inv_lines_ids)
#            
#            for line in res:
#                if line['product_id']:
#                    product_ids.append(line['product_id'][0])
            
            product_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', invoice_ids)], name = 'product_id')
            
            
            return set(product_ids)
        
        
        def invoice_2_prodlot(cr, uid, invoice_ids):
#            prodlot_ids = []
            sale_line_ids = []
            
            inv_line_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', invoice_ids)])
            if not inv_line_ids:
                return []                
            cr.execute("select order_line_id from sale_order_line_invoice_rel where invoice_id in ("+ ','.join(map(lambda x: str(x),inv_line_ids))+')')
            res = cr.fetchall()
            for i in res:
                for j in i:
                    sale_line_ids.append(j)
            
#            stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', 'in', sale_line_ids)])
#            res = self.pool.get('stock.move').read(cr, uid, stock_move_ids)
#            
#            for line in res:
#                if line['prodlot_id']:
#                    prodlot_ids.append(line['prodlot_id'][0])

            prodlot_ids  = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', 'in', sale_line_ids)], name = 'prodlot_id')
            
            return set(prodlot_ids)
        
        def prodlot_2_product(cr, uid, prodlot_ids):

            print prodlot_ids
#            product_ids = []            
#            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)])
#            if len (stock_move_ids)==0: 
#                print 'no prodlot sale'
#                return []
#            
#            print 'stock_move_ids', stock_move_ids
#            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids)
#            print res
#
#            for line in res:
#                if line['product_id']:
#                    product_ids.append(line['product_id'][0])   

            product_ids = self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)], name = 'product_id')
            
            return set(product_ids)
        
        
        def product_2_prodlot(cr, uid, product_ids):
            return set(self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)], name = 'prodlot_id'))
            
            
        def sale_line_2_invoice(cr, uid, sale_line_ids):
#            invoice_ids = []
#            sale_line_ids = []
            inv_line_ids = []
            
#            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids)
#            for line in res:
#                if line['sale_line_id']:
#                    sale_line_ids.append(line['sale_line_id'][0])

#            sale_line_ids = self.pool.get('stock.move').search(cr, uid, [('id', 'in', stock_move_ids)], name = 'sale_line_id')
            if not sale_line_ids:
                return []   
            cr.execute("select invoice_id from sale_order_line_invoice_rel where order_line_id in ("+ ','.join(map(lambda x: str(x),sale_line_ids))+')')
            res = cr.fetchall()     
            for i in res:
                for j in i:
                    inv_line_ids.append(j)
                    
#            res=self.pool.get('account.invoice.line').read(cr, uid, inv_line_ids)
#            for line in res:
#                if line['invoice_id']:
#                    invoice_ids.append(line['invoice_id'][0])

            invoice_ids = self.pool.get('account.invoice.line').search(cr, uid, [('id', 'in', inv_line_ids)], name = 'invoice_id')

            return invoice_ids
         
        
        def prodlot_2_invoice(cr, uid, prodlot_ids):

#            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)])
#            if len (stock_move_ids)==0:
#                print 'no prodlot sold'
#                return []
            sale_line_ids=self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)], name = 'sale_line_id')
            
            return set(sale_line_2_invoice(cr, uid, sale_line_ids))
        

        def product_2_invoice(cr, uid, product_ids):

#            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)])
#            if len (stock_move_ids)==0:
#                print 'no product sold'
#                return []
            
            sale_line_ids=self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)], name = 'sale_line_id')

            return set(sale_line_2_invoice(cr, uid, sale_line_ids))
        
        
        def invoice_2_partner(cr, uid, invoice_ids):
#            partner_ids = []
#            res=self.pool.get('account.invoice').read(cr, uid, invoice_ids)
#            for line in res:
#                if line['partner_id']:
#                    partner_ids.append(line['partner_id'][0])

            partner_ids=self.pool.get('account.invoice').search(cr, uid, [('id', 'in', invoice_ids)], name = 'partner_id')

                    
            return set(partner_ids)
         
        def partner_2_invoice(cr, uid, partner_ids):
            return set(self.pool.get('account.invoice').search(cr, uid, [('partner_id', 'in', partner_ids)]))
            

        
        
        product_ids=set([])
        prodlot_ids=set([])
        invoice_ids =set([])
        partner_ids =set([])
        
        print 'partner_id, invoice_id, product_id, prodlot_id', partner_id, invoice_id, product_id, prodlot_id
        print 'filtre', filtre
        
#probleme 
#choix d'un partner 
#--> création d'un domain et valeur sur les produits, les invoices, les prodlot
#puis choix d'un produit
#--> création d'un domain et valeur sur les invoices, les prodlot
#changement de produit
#-->les champs qui ont été complété par value reste et ne sont pas recalculer

        if not partner_id and not invoice_id and not product_id and not prodlot_id:
            filtre['value'] = {}
            filtre['domain'] = {}
            print 'clear'
            return filtre
            

        value = filtre['value'].copy()

        for field in value:
            if not filtre['value'][field]:
                del filtre['value'][field] 
        
        
        if filtre['value']:
            if filtre['value'].get('product_id', False):
                filtre['value']['product_id'] = False
                product_id = None
                
            if filtre['value'].get('prodlot_id', False):
                filtre['value']['prodlot_id'] = False
                prodlot_id = None
            if filtre['value'].get('invoice_id', False):
                filtre['value']['invoice_id'] = False
                invoice_id = None
            if filtre['value'].get('partner_id', False):
                filtre['value']['partner_id'] = False
                partner_id = None
        
        
        
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
        
        if invoice_ids:
            invoice_ids = [i for i in invoice_ids]
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

        if not product_id and len (product_ids) != 0:
            if len(product_ids)==1:
                print 'product value'
                filtre['value']['product_id'] = product_ids[0]
            else:
                print 'product domain'
                filtre['domain']['product_id']= "[('id','in', %s)]" % product_ids
                
        if not prodlot_id and len (prodlot_ids) != 0:
            if len(prodlot_ids)==1:
                print 'prodlot value'
                filtre['value']['prodlot_id'] = prodlot_ids[0]
            else:
                print 'prodlot domain'
                filtre['domain']['prodlot_id']= "[('id','in', %s)]" % prodlot_ids

        if not invoice_id and len (invoice_ids) != 0:
            if len(invoice_ids)==1:
                print 'invoice value'
                filtre['value']['invoice_id'] = invoice_ids[0]
            else:
                print 'invoice domain'
                filtre['domain']['invoice_id']= "[('id','in', %s)]" % invoice_ids
                
        if not partner_id and len (partner_ids) != 0:
            if len(partner_ids)==1:
                print 'partner value'
                filtre['value']['partner_id'] = partner_ids[0]
            else:
                print 'partner domain'
                filtre['domain']['partner_id']= "[('id','in', %s)]" % partner_ids

        print filtre

        return filtre
    
    
    
    
    

crm_case()
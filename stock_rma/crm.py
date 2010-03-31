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
from datetime import datetime
from dateutil.relativedelta import relativedelta

class crm_rma(osv.osv):
    _inherits = {'crm.case': 'crm_id'}
    _name = "crm.rma"
    _columns = {
        'crm_id': fields.many2one('crm.case', 'CRM case', required=True),
        'rma_ref': fields.char('Incident Ref', size=64, required=True, select=1),
        'incoming_picking_id': fields.many2one('stock.picking', 'Incoming Picking', required=False, select=1),
        'outgoing_picking_id': fields.many2one('stock.picking', 'Outgoing Picking', required=False, select=True),
        'related_incoming_picking_state': fields.related('incoming_picking_id', 'state', type="char", string="Related Picking State", readonly=True),
        'related_outgoing_picking_state': fields.related('outgoing_picking_id', 'state', type="char", string="Related Picking State", readonly=True),
        'in_supplier_picking_id': fields.many2one('stock.picking', 'Return To Supplier Picking', required=False, select=True),
        'out_supplier_picking_id': fields.many2one('stock.picking', 'Return From Supplier Picking', required=False, select=True),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial / Lot Number'),
        'product_id': fields.many2one('product.product', 'Product'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'new_invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'warning': fields.char('Warning', size=64, select=1, readonly=True),
        'guarantee_limit': fields.date('Warranty limit', help="The warranty limit is computed as: invoice date + warranty defined on selected product.", readonly=True),
        'extra_note': fields.text('Note'),
         #IT WILL BE BETTER TO USE warranty_limit THEN guarantee_limit BUT WE CHOOSE THIS NAME IN ORDER TO BE COMPATIBLE WITH THE MODULE MRP_REPAIR
    }
    
    _defaults = {
        'rma_ref': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'rma'),
    }


    #here we decorate the crm.case actions/methods. It sucks that OpenObject doesn't do it by default when using _inherits

    def onchange_partner_address_id(self, cr, uid, ids, part, email=False):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').onchange_partner_address_id(cr, uid, ids, part, email)
    
    def onchange_categ_id(self, cr, uid, ids, categ, context={}):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').onchange_categ_id(cr, uid, ids, categ, context)
    
    def case_close(self, cr, uid, ids, *args):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').case_close(cr, uid, ids, *args)

    def case_escalate(self, cr, uid, ids, *args):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').case_escalate(cr, uid, ids, *args)
    
    def case_open(self, cr, uid, ids, *args):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').case_open(cr, uid, ids, *args)
    
    def case_cancel(self, cr, uid, ids, *args):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').case_cancel(cr, uid, ids, *args)
    
    def case_pending(self, cr, uid, ids, *args):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').case_pending(cr, uid, ids, *args)
    
    def case_reset(self, cr, uid, ids, *args):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').case_reset(cr, uid, ids, *args)
    
    def stage_next(self, cr, uid, ids, context={}):
        ids = [self.pool.get('crm.rma').browse(cr, uid, id).crm_id.id for id in ids]
        return self.pool.get('crm.case').stage_next(cr, uid, ids, context)



    global parent
    parent = {}

    def onchange_form(self, cr, uid, ids, action, partner_id, invoice_id, product_id, prodlot_id):
        
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
            return set([x['prodlot_id'][0] for x in res if x['prodlot_id']])
        
        def prodlot_2_product(cr, uid, prodlot_ids):          
            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('prodlot_id', 'in', prodlot_ids)])
            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids, ['product_id'])
            return set([x['product_id'][0] for x in res if x['product_id']])
        
        def product_2_prodlot(cr, uid, product_ids):
            stock_move_ids=self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)])
            res=self.pool.get('stock.move').read(cr, uid, stock_move_ids, ['prodlot_id'])
            return set([x['prodlot_id'][0] for x in res if x['prodlot_id']])
            
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
                    
        def find_ids(cr, uid, dico):
            for field_2_convert in dico:
                if id[field_2_convert]:
                    for key in dico[field_2_convert]:
                        if not id[key]:
                            if res_ids[key]:
                                res_ids[key] = res_ids[key].intersection(dico[field_2_convert][key](cr, uid, id[field_2_convert]))
                            else:
                                res_ids[key] = dico[field_2_convert][key](cr, uid, id[field_2_convert])
            return

        id = {'partner':partner_id, 'invoice':invoice_id, 'product':product_id, 'prodlot':prodlot_id}

        #removes fields which have for parent the field which launch the on change and convert each field to a table
        if parent:
            for key in id:
                if action in parent[uid][key] or not id[key]:
                    id[key] = []
                else:
                    id[key] = [id[key]]
                
        #Init the onchange
        if not parent or not id['partner'] and not id['invoice'] and not id['product'] and not id['prodlot']:
            parent[uid]={'partner' : {}, 'invoice' : {}, 'product' : {}, 'prodlot':{}}
            return {'value':{'partner_id' : False, 'invoice_id' : False, 'product_id':False, 'prodlot_id' : False, 'guarantee_limit' : False, 'warning' : False },
                     'domain':{'partner_id': '[]', 'invoice_id':'[]', 'product_id':'[]', 'prodlot_id':'[]'}}
        
        res_ids={'partner':[], 'invoice':[], 'product':[], 'prodlot':[]}
        filter = {'value':{'guarantee_limit' : False, 'warning' : False }, 'domain':{}}

        # starts to find all of ids in function of the existing field
        find_ids(cr, uid, {'partner': {'invoice' : partner_2_invoice},
                           'invoice': {'partner' : invoice_2_partner, 'product' : invoice_2_product, 'prodlot' : invoice_2_prodlot},
                           'product': {'invoice' : product_2_invoice, 'prodlot' :  product_2_prodlot},
                           'prodlot': {'invoice' :  prodlot_2_invoice, 'product' :  prodlot_2_product}})

        id['invoice_ids'] = [i for i in res_ids['invoice']]
        find_ids(cr, uid,{'invoice_ids': {'partner' : invoice_2_partner, 'product' : invoice_2_product, 'prodlot' : invoice_2_prodlot}})

        for key in res_ids:
            res_ids[key] = [i for i in res_ids[key]]

        #result are transformed in domain and value filter
        for key in res_ids:
            if not id[key]:
                parent[uid][key] = [ x for x in id if id.get(x,False) and x != 'invoice_ids']
                filter['domain'][key + '_id']= "[('id','in', %s)]" % res_ids[key]
                if len(res_ids[key])==1:
                    filter['value'][key + '_id'] = res_ids[key][0]
                    id[key] = res_ids[key]
                else:
                    filter['value'][key + '_id'] = False
        
        if id['invoice'] and id['product']:
            invoice_date = self.pool.get('account.invoice').read(cr, uid, id['invoice'],['date_invoice'])[0]['date_invoice']
            product_warranty = self.pool.get('product.product').read(cr, uid, id['product'],['warranty'])[0]['warranty']
            end_warranty = (datetime.strptime(invoice_date, '%Y-%m-%d') + relativedelta(months=int(product_warranty)))
            filter['value']['guarantee_limit'] = end_warranty.strftime('%Y-%m-%d')
            if end_warranty < datetime.now():
                filter['value']['warning'] = 'Warning the warranty is expired ! ! !'

        return filter

crm_rma()
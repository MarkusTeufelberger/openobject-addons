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

from mx import DateTime
from osv import fields,osv
from tools import config
from tools.translate import _
import netsvc
import time

class mrp_procurement(osv.osv):
    """Mrp Procurement"""
    
    _inherit="mrp.procurement"

    def action_po_assign(self, cr, uid, ids, context=None):
        """Find cheapest supplier"""
        
        if not context:
            context = {}
        purchase_id = False
        user_obj = self.pool.get('res.users')
        prod_obj = self.pool.get('product.product')
        prod_uom_obj = self.pool.get('product.uom')
        res_obj = self.pool.get('res.partner')
        prod_price_obj = self.pool.get('product.pricelist')
        acc_fiscal_obj = self.pool.get('account.fiscal.position')
        purchase_obj = self.pool.get('purchase.order')
        partner_price_obj = self.pool.get('pricelist.partnerinfo')
        company = user_obj.browse(cr, uid, uid, context).company_id
        for procurement in self.browse(cr, uid, ids):
            res_id = procurement.move_id.id
            uom_id = procurement.product_id.uom_po_id.id
            qty = prod_uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
            # Choose appropiate supplier
            partner = False
            partner_price = None
            partner_qty = False
            partner_delay = False
            factor = False
            min_qty = None
            list_supplier = []
            for supplier in procurement.product_id.seller_ids:
                price_ids = partner_price_obj.search(cr, uid, [('min_quantity', '=', qty), ('suppinfo_id', '=', supplier.id)])
                if price_ids:
                   for partner_pricelist in partner_price_obj.browse(cr, uid, price_ids):
                         factor = partner_pricelist.price
                         min_qty = partner_pricelist.min_quantity
                else:
                   price_ids = partner_price_obj.search(cr, uid, [('min_quantity', '<', qty), ('suppinfo_id', '=', supplier.id)])
                   if price_ids:
                       for partner_pricelist in partner_price_obj.browse(cr, uid, price_ids):
                           factor = partner_pricelist.price                         
                           min_qty = partner_pricelist.min_quantity
                list_supplier.append((supplier.name, factor, supplier.delay, min_qty))
            #Calculating price through sorting.
            list_supplier.sort(key=lambda a:a[1])
            #Find cheapest supplier
            partner= list_supplier[0][0]
            new_date = DateTime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S')
            for supplier in list_supplier:
                delay_date = DateTime.now()+ DateTime.RelativeDateTime(days=supplier[2])
                if delay_date <= new_date: 
                    partner = supplier[0]
                    partner_delay = supplier[2]
                    partner_qty = supplier[3]
                    break

            if partner:                                       
                partner_id = partner.id
                address_id = res_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                pricelist_id = partner.property_product_pricelist_purchase.id
                if partner_qty: 
                    qty=max(qty, partner_qty)
    
                price = prod_price_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, False, {'uom': uom_id})[pricelist_id]
                newdate = DateTime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S')
                newdate = newdate - DateTime.RelativeDateTime(days=company.po_lead)
                newdate = newdate - partner_delay
                #Passing partner_id to context for purchase order line integrity of Line name
                context.update({'lang':partner.lang, 'partner_id':partner_id})
                
                product=prod_obj.browse(cr,uid,procurement.product_id.id,context=context)
    
                line = {
                    'name': product.partner_ref,
                    'product_qty': qty,
                    'product_id': procurement.product_id.id,
                    'product_uom': uom_id,
                    'price_unit': price,
                    'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                    'move_dest_id': res_id,
                    'notes':product.description_purchase,
                }
    
                taxes_ids = procurement.product_id.product_tmpl_id.supplier_taxes_id
                taxes = acc_fiscal_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
                line.update({
                    'taxes_id':[(6,0,taxes)]
                })
                purchase_id = purchase_obj.create(cr, uid, {
                    'origin': procurement.origin,
                    'partner_id': partner_id,
                    'partner_address_id': address_id,
                    'location_id': procurement.location_id.id,
                    'pricelist_id': pricelist_id,
                    'order_line': [(0,0,line)],
                    'fiscal_position': partner.property_account_position and partner.property_account_position.id or False
                })
                self.write(cr, uid, [procurement.id], {'state':'running', 'purchase_id':purchase_id})
        return purchase_id

mrp_procurement()
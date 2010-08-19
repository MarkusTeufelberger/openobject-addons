# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. - All Rights Reserved.
#                    http://www.NaN-tic.com
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

from mx import DateTime

from osv import osv
from osv import fields
from tools.translate import _

class mrp_procurement(osv.osv):
    _inherit = 'mrp.procurement'

    def action_po_assign(self, cr, uid, ids, context={}):
        purchase_id = False
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        for procurement in self.browse(cr, uid, ids):
            res_id = procurement.move_id.id

            uom_id = procurement.product_id.uom_po_id.id

            qty = self.pool.get('product.uom')._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)

            # Choose appropiate supplier
            partner = procurement.product_id.seller_ids[0].name
            partner_price = None
            partner_qty = procurement.product_id.seller_ids[0].qty
            partner_delay = procurement.product_id.seller_ids[0].delay
            for supplier in procurement.product_id.seller_ids:
                for pricelist in supplier.pricelist_ids:
                    if pricelist.valid and qty >= pricelist.min_quantity and (not partner_price or partner_price < pricelist.price):
                        partner = supplier.name
                        partner_price = pricelist.price
                        partner_qty = pricelist.min_quantity
                        partner_delay = supplier.delay

            partner_id = partner.id
            address_id = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id

            if partner_qty: 
                qty=max(qty, partner_qty)

            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, False, {'uom': uom_id})[pricelist_id]

            newdate = DateTime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S')
            newdate = newdate - DateTime.RelativeDateTime(days=company.po_lead)
            newdate = newdate - partner_delay

            #Passing partner_id to context for purchase order line integrity of Line name
            context.update({'lang':partner.lang, 'partner_id':partner_id})
            
            product=self.pool.get('product.product').browse(cr,uid,procurement.product_id.id,context=context)

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
            taxes = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, taxes_ids)
            line.update({
                'taxes_id':[(6,0,taxes)]
            })
            purchase_id = self.pool.get('purchase.order').create(cr, uid, {
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

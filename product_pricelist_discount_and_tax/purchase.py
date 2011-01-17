# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2010-2011 Gábor Dukai (gdukai@gmail.com)
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

import time
from mx import DateTime

from osv import osv
from tools.translate import _

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'

    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False, fiscal_position=False):
        """Original overridden to call price_get_improved() instead of price_get()
        and set the discount field."""
        if not pricelist:
            raise osv.except_osv(_('No Pricelist !'), _('You have to select a pricelist in the purchase form !\nPlease set one before choosing a product.'))
        if not  partner_id:
            raise osv.except_osv(_('No Partner!'), _('You have to select a partner in the purchase form !\nPlease set one partner before choosing a product.'))
        if not product:
            return {'value': {'price_unit': 0.0, 'name':'','notes':'', 'product_uom' : False}, 'domain':{'product_uom':[]}}
        lang=False
        if partner_id:
            lang=self.pool.get('res.partner').read(cr, uid, partner_id)['lang']
        context={'lang':lang}
        context['partner_id'] = partner_id

        prod = self.pool.get('product.product').browse(cr, uid, product, context=context)
        prod_uom_po = prod.uom_po_id.id
        if not uom:
            uom = prod_uom_po
        if not date_order:
            date_order = time.strftime('%Y-%m-%d')

        qty = qty or 1.0
        seller_delay = 0
        for s in prod.seller_ids:
            if s.name.id == partner_id:
                seller_delay = s.delay
                temp_qty = s.qty # supplier _qty assigned to temp
                if qty < temp_qty: # If the supplier quantity is greater than entered from user, set minimal.
                    qty = temp_qty

        price_res = self.pool.get('product.pricelist').price_get_improved\
            (cr,uid,[pricelist], product, qty or 1.0, partner_id, {
                    'uom': uom,
                    'date': date_order,
                    })[pricelist]
        price = price_res['price']
        dt = (DateTime.now() + DateTime.RelativeDateTime(days=int(seller_delay) or 0.0)).strftime('%Y-%m-%d %H:%M:%S')
        prod_name = prod.partner_ref


        res = {'value': {'price_unit': price, 'name':prod_name, 'taxes_id':map(lambda x: x.id, prod.supplier_taxes_id),
            'date_planned': dt,'notes':prod.description_purchase,
            'product_qty': qty,
            'product_uom': uom}}
        #dukai
        if 'discount' in price_res:
            res['value']['discount'] = price_res['discount']

        taxes = self.pool.get('account.tax').browse(cr, uid,map(lambda x: x.id, prod.supplier_taxes_id))
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        res['value']['taxes_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)

        res2 = self.pool.get('product.uom').read(cr, uid, [uom], ['category_id'])
        res3 = prod.uom_id.category_id.id
        domain = {'product_uom':[('category_id','=',res2[0]['category_id'][0])]}
        if res2[0]['category_id'][0] != res3:
            raise osv.except_osv(_('Wrong Product UOM !'), _('You have to select a product UOM in the same category than the purchase UOM of the product'))

        res['domain'] = domain
        return res

purchase_order_line()

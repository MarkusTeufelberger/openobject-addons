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

from osv import osv
from tools.translate import _

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False):
        """Original overridden to call price_get_improved() instead of price_get()
        and set the discount field."""
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined !'), _('You have to select a customer in the sale form !\nPlease set one customer before choosing a product.'))
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context = {'lang': lang, 'partner_id': partner_id}
        if not product:
            return {'value': {'th_weight': 0, 'product_packaging': False,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}

        if not date_order:
            date_order = time.strftime('%Y-%m-%d')

        result = {}
        product_obj = product_obj.browse(cr, uid, product, context=context)
        if not packaging and product_obj.packaging:
            packaging = product_obj.packaging[0].id
            result['product_packaging'] = packaging

        if packaging:
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            pack = self.pool.get('product.packaging').browse(cr, uid, packaging, context)
            q = product_uom_obj._compute_qty(cr, uid, uom, pack.qty, default_uom)
#            qty = qty - qty % q + q
            if qty and (q and not (qty % q) == 0):
                ean = pack.ean
                qty_pack = pack.qty
                type_ul = pack.ul
                warn_msg = _("You selected a quantity of %d Units.\nBut it's not compatible with the selected packaging.\nHere is a proposition of quantities according to the packaging: ") % (qty)
                warn_msg = warn_msg + "\n\n" + _("EAN: ") + str(ean) + _(" Quantity: ") + str(qty_pack) + _(" Type of ul: ") + str(type_ul.name)
                warning = {
                    'title': _('Packing Information !'),
                    'message': warn_msg
                    }
            result['product_uom_qty'] = qty

        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False

        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        result.update({'type': product_obj.procure_method})
        if product_obj.description_sale:
            result['notes'] = product_obj.description_sale
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['delay'] = (product_obj.sale_delay or 0.0)
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)
        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context)[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}

        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        # get unit price

        if not pricelist:
            warning = {
                'title': 'No Pricelist !',
                'message':
                    'You have to select a pricelist in the sale form !\n'
                    'Please set one before choosing a product.'
                }
        else:
            #dukai
            price_res = self.pool.get('product.pricelist').price_get_improved\
                (cr, uid, [pricelist], product, qty or 1.0, partner_id, {
                        'uom': uom,
                        'date': date_order,
                        })[pricelist]
            price = price_res['price']
            if price is False:
                warning = {
                    'title': 'No valid pricelist line found !',
                    'message':
                        "Couldn't find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist."
                    }
            else:
                result.update({'price_unit': price})
                #dukai
                if 'discount' in price_res:
                    result.update({'discount': price_res['discount']})
        return {'value': result, 'domain': domain, 'warning': warning}

sale_order_line()
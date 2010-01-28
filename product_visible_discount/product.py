# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
from osv import fields, osv
import pooler
from tools import config
import time
from osv.osv import except_osv
from tools.translate import _

class product_pricelist(osv.osv):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'
    _columns ={
        'visible_discount':fields.boolean('Visible Discount'),
    }

    _defaults = {
         'visible_discount':lambda *a: True,
   }
product_pricelist()

class sale_order_line(osv.osv):
    _name = "sale.order.line"
    _inherit = "sale.order.line"

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True,date_order=False,packaging=False,fiscal_position=False, flag=False):
        res=super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax,date_order,fiscal_position=fiscal_position,flag=flag)

        context = {'lang': lang, 'partner_id': partner_id}
        result=res['value']
        pricelist_obj=self.pool.get('product.pricelist')
        product_obj = self.pool.get('product.product')
        if product:
            if result.get('price_unit',False):
                price=result['price_unit']
            else:
                return res

            product = product_obj.browse(cr, uid, product, context)
            product_tmpl_id = product.product_tmpl_id.id
            pricetype_id = pricelist_obj.browse(cr, uid, pricelist).version_id[0].items_id[0].base
            field_name = 'list_price'
            product_read = self.pool.get('product.template').read(cr, uid, product_tmpl_id, [field_name], context)
            list_price = product_read[field_name]


            pricelists=pricelist_obj.read(cr,uid,[pricelist],['visible_discount'])

            old_uom = product.uos_id or product.uom_id
            new_list_price = self.pool.get('product.uom')._compute_price(cr,
                        uid, old_uom.id, list_price, uom)
            if(len(pricelists)>0 and pricelists[0]['visible_discount'] and list_price != 0):
                discount=(new_list_price-price) / new_list_price * 100
                result['price_unit']=new_list_price
                result['discount']=discount
            else:
                result['discount']=0.0
        return res



sale_order_line()

class account_invoice_line(osv.osv):
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, context={}):
        res=super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom, qty, name, type, partner_id, fposition_id, price_unit, address_invoice_id, context)


        def get_real_price(pricelist_id, product_id):
            product_tmpl_id = self.pool.get('product.product').browse(cr, uid, product_id, context).product_tmpl_id.id
            version_id = self.pool.get('product.pricelist').browse(cr, uid, pricelist_id).version_id
            version_id = version_id and version_id[0] or False
            
            if not version_id:
                raise osv.except_osv(_('No Pricelist Version Found !'),_("You must first define Pricelist Version to the Partner Pricelist!"))
            else:
                items = version_id.items_id
                
                if not items:
                    raise osv.except_osv(_('No Pricelist ListPrice Items Found !'),_("You must first define ListPrice Items to Pricelist Version of the Partner Pricelist!"))
                else:
                    pricetype_id = items[0].base
                    
            if pricetype_id > 0:
                field_name = self.pool.get('product.price.type').browse(cr, uid, pricetype_id).field
            else:
                field_name= 'list_price'
                
            product_read = self.pool.get('product.template').read(cr, uid, product_tmpl_id, [field_name], context)
            return product_read[field_name]

        
        if product:
            product = self.pool.get('product.product').browse(cr, uid, product, context=context)
            result=res['value']
            pricelist = False
            real_price = 0.00
            if type in ('in_invoice', 'in_refund'):
                if not price_unit and partner_id:
                    pricelist = self.pool.get('res.partner').browse(cr, uid, partner_id).property_product_pricelist_purchase.id
                    if not pricelist:
                        raise osv.except_osv(_('No Purchase Pricelist Found !'),_("You must first define a pricelist for Supplier !"))
                    price_unit = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product.id, qty or 1.0, partner_id, {'uom': uom})[pricelist]
                    real_price=get_real_price(pricelist, product.id)
            else:
                if partner_id:
                    pricelist = self.pool.get('res.partner').browse(cr, uid, partner_id).property_product_pricelist.id
                    if not pricelist:
                        raise osv.except_osv(_('No Sale Pricelist Found '),_("You must first define a pricelist for Customer !"))
                    price_unit = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product.id, qty or 1.0, partner_id, {'uom': uom})[pricelist]
                    real_price=get_real_price(pricelist, product.id)
            if pricelist:
                pricelists=self.pool.get('product.pricelist').read(cr,uid,[pricelist],['visible_discount'])
                if(len(pricelists)>0 and pricelists[0]['visible_discount'] and real_price != 0):
                    discount=(real_price-price_unit) / real_price * 100
                    result['price_unit']=real_price
                    result['discount']=discount
                else:
                    result['discount']=0.0
        return res


account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


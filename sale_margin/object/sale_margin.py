# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_margin module for OpenERP, add margin in sale order and invoice
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2009 EVERLIBRE (<http://www.Everlibre.fr>) Éric VERNICHON
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
#
#    This file is a part of sale_margin
#
#    sale_margin is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_margin is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields,osv
import pooler
from tools import config
import time

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    def convert_to_foreign_currency(self, cr, uid, pricelist, amount):
        pricelist_obj = self.pool.get('product.pricelist').browse(cr, uid, pricelist)
        company_currency = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        price = self.pool.get('res.currency').compute(cr, uid, company_currency, pricelist_obj.currency_id.id, amount, round=False)
        return price
    
    def price_unit_change(self, cr, uid, ids, purchase_price, product_uom_qty, product_uos_qty, price_unit, product, discount, pricelist):
        """If price unit change, calcul the new margin.
        :param pv: sale price
        :param pa: purchase price
        :param margin: amount margin"""

        res = {}
        res['value'] = {}
        if product:
            product_tmpl_obj = self.pool.get('product.template')
            product_obj = self.pool.get('product.product')
            pr = product_obj.read(cr,uid,product)
            product_value = product_tmpl_obj.read(cr,uid,pr['product_tmpl_id'][0])
            std_price = self.convert_to_foreign_currency(cr, uid, pricelist, product_value['standard_price'])
            pv = (price_unit*product_uom_qty*(100.0-discount)/100.0)
            pa = (std_price*product_uom_qty)
            margin = round(pv -pa,int(config['price_accuracy']))
            res['value']['margin'] = margin
            res['value']['marginpourcent'] = (((pv-pa)/pv)*100)
            res['value']['purchase_price'] = std_price
        return res

    def discount_change(self, cr, uid, ids, purchase_price, product_uom_qty, product_uos_qty, price_unit, product, discount, pricelist):
        """If discount change, calcul the new margin.
        :param pv: sale price
        :param pa: purchase price
        :param margin: amount margin"""

        res = {}
        res['value'] = {}
        if product:
            product_tmpl_obj = self.pool.get('product.template')
            product_obj = self.pool.get('product.product')
            pr = product_obj.read(cr,uid,product)
            product_value = product_tmpl_obj.read(cr,uid,pr['product_tmpl_id'][0])
            std_price = self.convert_to_foreign_currency(cr, uid, pricelist, product_value['standard_price'])
            pv = (price_unit*product_uom_qty*(100.0-discount)/100.0)
            pa = (std_price*product_uom_qty)
            margin = round(pv -pa,int(config['price_accuracy']))
            res['value']['margin'] = margin
            res['value']['marginpourcent'] = (((pv-pa)/pv)*100)
            res['value']['purchase_price'] = std_price
        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,uom=False, qty_uos=0, uos=False, name='', partner_id=False,lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False,discount=0.0,price_unit=0.0):
        """If product change, calcul the new margin.
        :param pv: sale price
        :param pa: purchase price
        :param margin: amount margin"""

        temp = {}
        temp['product'] = ''
        if price_unit>0:
            temp['price_unit'] = price_unit
            if product:
                temp['product'] = product
        res = super(sale_order_line, self).product_id_change( cr, uid, ids, pricelist, product,qty,uom,qty_uos,uos,name,partner_id,lang,update_tax,date_order,packaging,fiscal_position,flag)
        if product:
            if product==temp['product']:
                res['value']['price_unit']=price_unit
            product_tmpl_obj = self.pool.get('product.template')
            product_obj = self.pool.get('product.product')
            pr = product_obj.read(cr,uid,product)
            product_value = product_tmpl_obj.read(cr,uid,pr['product_tmpl_id'][0] )
            std_price = self.convert_to_foreign_currency(cr, uid, pricelist, product_value['standard_price'])
            pv = (res['value']['price_unit']*res['value']['product_uos_qty']*(100.0-discount)/100.0)
            pa = (std_price*res['value']['product_uos_qty'])
            margin = round(pv - pa,int(config['price_accuracy']))
            res['value']['margin'] = margin
            res['value']['marginpourcent'] = (((pv-pa)/pv)*100)
            res['value']['purchase_price'] = std_price

        return res

    _columns = {
        'margin': fields.float('Margin',digits=(16, int(config['price_accuracy']))),
        'marginpourcent': fields.float('Margin %',digits=(16, int(config['price_accuracy']))),
        'purchase_price': fields.float('Cost Price', digits=(16, int(config['price_accuracy']))),
    }

sale_order_line()

class sale_order(osv.osv):
    _inherit = "sale.order"

    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        """Calculate the amount total of margin"""

        res = {}
        res=super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context)
        for order in self.browse(cr, uid, ids):
            val = 0.0

            for line in order.order_line:
                val += line.margin
            res[order.id]['margin'] = val
        return res

    def _get_order(self, cr, uid, ids, context={}):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'margin':  fields.function(_amount_all, method=True, string='Margin',multi='sums',digits=(16, int(config['price_accuracy']))),
        'amount_untaxed': fields.function(_amount_all, method=True, string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums',digits=(16, int(config['price_accuracy']))),
        'amount_tax': fields.function(_amount_all, method=True, string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'amount_total': fields.function(_amount_all, method=True, string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums',digits=(16, int(config['price_accuracy']))),
    }

sale_order()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'invoice_ids': fields.many2many('account.invoice', 'picking_invoice_rel', 'picking_id', 'invoice_id', 'Invoices', domain=[('type','=','in_invoice')]),
    }

    def create_invoice(self, cr, uid, ids, *args):
        # need to carify with new requirement
        res = False
        invoice_ids = []
        margin_deduce = 0.0
        picking_obj = self.pool.get('stock.picking')
        picking_obj.write(cr, uid, ids, {'invoice_state' : '2binvoiced'})
        res = picking_obj.action_invoice_create(cr, uid, ids, type='out_invoice', context={})
        invoice_ids = res.values()
        picking_obj.write(cr, uid, ids,{'invoice_ids':[[6,0,invoice_ids]]})
        return True

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from __future__ import division
import time

from osv import fields, osv
from tools.translate import _
from _common import rounding

class price_type(osv.osv):
    _inherit = 'product.price.type'

    _columns = {
        'price_tax_included': fields.boolean('Price Tax Included'),
    }

price_type()

class product_pricelist(osv.osv):
    _inherit = 'product.pricelist'

    _columns = {
        'visible_discount': fields.boolean('Visible Discount'),
        'price_tax_included': fields.boolean('Price Tax Included'),
    }

    _defaults = {
         'visible_discount': lambda *a: True,
    }

    def price_get_improved(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        '''
        This is a copy of the price_get() method from the product module. It returns
        {'price': price,
         'base': base of that price,
         'price_tax_include': is tax included in that resulted price}
        dictionaries instead of a plain price.

        context = {
            'uom': Unit of Measure (int),
            'partner': Partner ID (int),
            'date': Date of the pricelist (%Y-%m-%d),
        }
        '''
        context = context or {}
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        if context and ('partner_id' in context):
            partner = context['partner_id']
        context['partner_id'] = partner
        date = time.strftime('%Y-%m-%d')
        if context and ('date' in context):
            date = context['date']
        result = {}
        for id in ids:
            cr.execute('SELECT * ' \
                    'FROM product_pricelist_version ' \
                    'WHERE pricelist_id = %s AND active=True ' \
                        'AND (date_start IS NULL OR date_start <= %s) ' \
                        'AND (date_end IS NULL OR date_end >= %s) ' \
                    'ORDER BY id LIMIT 1', (id, date, date))
            plversion = cr.dictfetchone()

            if not plversion:
                raise osv.except_osv(_('Warning !'),
                        _('No active version for the selected pricelist !\n' \
                                'Please create or activate one.'))

            cr.execute('SELECT id, categ_id ' \
                    'FROM product_template ' \
                    'WHERE id = (SELECT product_tmpl_id ' \
                        'FROM product_product ' \
                        'WHERE id = %s)', (prod_id,))
            tmpl_id, categ = cr.fetchone()
            categ_ids = []
            while categ:
                categ_ids.append(str(categ))
                cr.execute('SELECT parent_id ' \
                        'FROM product_category ' \
                        'WHERE id = %s', (categ,))
                categ = cr.fetchone()[0]
                if str(categ) in categ_ids:
                    raise osv.except_osv(_('Warning !'),
                            _('Could not resolve product category, ' \
                                    'you have defined cyclic categories ' \
                                    'of products!'))
            if categ_ids:
                categ_where = '(categ_id IN %s)'
                sqlargs = (tuple(categ_ids),)
            else:
                categ_where = '(categ_id IS NULL)'
                sqlargs = ()

            cr.execute(
                #dukai - price_tax_included, visible_discount
                'SELECT i.*, pl.currency_id, pl.price_tax_included, '
                '    pl.visible_discount '
                'FROM product_pricelist_item AS i, '
                    'product_pricelist_version AS v, product_pricelist AS pl '
                'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                    'AND (product_id IS NULL OR product_id = %s) '
                    'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                    'AND price_version_id = %s '
                    'AND (min_quantity IS NULL OR min_quantity <= %s) '
                    'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                'ORDER BY sequence LIMIT 1',
                (tmpl_id, prod_id) + sqlargs + ( plversion['id'], qty))
            res = cr.dictfetchone()
            if res:
                #dukai
                base_price_tax_included = False
                if res['base'] == -1:
                    if not res['base_pricelist_id']:
                        price = 0.0
                    else:
                        #dukai
                        res2 = self.price_get_improved(cr, uid,
                                [res['base_pricelist_id']], prod_id,
                                qty, context=context)[res['base_pricelist_id']]
                        ptype_src = self.browse(cr, uid,
                                res['base_pricelist_id']).currency_id.id
                        price = currency_obj.compute(cr, uid, ptype_src,
                                res['currency_id'], res2['price'], round=False)
                        base_price_tax_included = res2['price_tax_included']
                elif res['base'] == -2:
                    where = []
                    if partner:
                        where = [('name', '=', partner) ]
                    sinfo = supplierinfo_obj.search(cr, uid,
                            [('product_id', '=', tmpl_id)] + where)
                    price = 0.0
                    if sinfo:
                        cr.execute('SELECT * ' \
                                'FROM pricelist_partnerinfo ' \
                                'WHERE suppinfo_id IN %s ' \
                                    'AND min_quantity <= %s ' \
                                'ORDER BY min_quantity DESC LIMIT 1',
                                   (tuple(sinfo), qty))
                        res2 = cr.dictfetchone()
                        if res2:
                            price = res2['price']
                            #dukai
                            base_price_tax_included = False
                else:
                    price_type = price_type_obj.browse(cr, uid, int(res['base']))
                    price = currency_obj.compute(cr, uid,
                            price_type.currency_id.id, res['currency_id'],
                            product_obj.price_get(cr, uid, [prod_id],
                                price_type.field)[prod_id], round=False, context=context)
                    #dukai
                    base_price_tax_included = price_type.price_tax_included

                #dukai
                if res['price_tax_included'] and not base_price_tax_included:
                    tax_obj = self.pool.get('account.tax')
                    prod = product_obj.browse(cr, uid, prod_id)
                    for tax in tax_obj.compute(cr, uid, prod.taxes_id,
                        price, 1):
                        price += tax['amount']
                if not res['price_tax_included'] and base_price_tax_included:
                    tax_obj = self.pool.get('account.tax')
                    prod = product_obj.browse(cr, uid, prod_id)
                    for tax in tax_obj.compute_inv(cr, uid, prod.taxes_id,
                        price, 1):
                        price -= tax['amount']

                price_limit = price

                price = price * (1.0+(res['price_discount'] or 0.0))
                price = rounding(price, res['price_round'])
                price += (res['price_surcharge'] or 0.0)
                if res['price_min_margin']:
                    price = max(price, price_limit+res['price_min_margin'])
                if res['price_max_margin']:
                    price = min(price, price_limit+res['price_max_margin'])
            else:
                # False means no valid line found ! But we may not raise an
                # exception here because it breaks the search
                price = False
            result[id] = {
                'price': price,
                'price_tax_included': res and res['price_tax_included'] or False,
                }
            if price and res['visible_discount']:
                result[id].update({
                    'price': price_limit,
                    'discount': (price_limit - price) / price_limit * 100,
                })
            if context and ('uom' in context):
                product = product_obj.browse(cr, uid, prod_id)
                uom = product.uos_id or product.uom_id
                #dukai
                uom_obj = self.pool.get('product.uom')
                for k in result[id]:
                    result[id][k] = uom_obj._compute_price(cr,
                        uid, uom.id, result[id][k], context['uom'])
        return result

product_pricelist()

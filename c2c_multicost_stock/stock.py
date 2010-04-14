# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camtocamp SA
# @author Joël Grand-Guillaume
# $Id: $
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
import time
import netsvc
from osv import fields, osv
from tools import config
from tools.translate import _
import tools

#----------------------------------------------------------
# Stock Location
#----------------------------------------------------------
class stock_location(osv.osv):
    _inherit = "stock.location"

    def product_detail(self, cr, uid, id, field, context={}):
        res = {}
        res[id] = {}
        final_value = 0.0
        field_to_read = 'virtual_available'
        if field == 'stock_real_value':
            field_to_read = 'qty_available'
        cr.execute('select distinct product_id from stock_move where (location_id=%s) or (location_dest_id=%s)', (id, id))
        result = cr.dictfetchall()
        if result:
               # Choose the right filed standard_price to read
               # Take the user company
               price_type_id=self.pool.get('res.users').browse(cr,uid,uid).company_id.property_valuation_price_type.id
               pricetype=self.pool.get('product.price.type').browse(cr,uid,price_type_id)
               
               for r in result:
                   c = (context or {}).copy()
                   c['location'] = id
                   product = self.pool.get('product.product').read(cr, uid, r['product_id'], [field_to_read], context=c)
                   # Compute the amount_unit in right currency
                   
                   context['currency_id']=self.pool.get('res.users').browse(cr,uid,uid).company_id.currency_id.id
                   amount_unit=self.pool.get('product.product').browse(cr,uid,r['product_id']).price_get(pricetype.field, context)[r['product_id']]
                   
                   final_value += (product[field_to_read] * amount_unit)
        return final_value

    def _product_get_report(self, cr, uid, ids, product_ids=False,
            context=None, recursive=False):
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        # Take the user company and pricetype
        price_type_id=self.pool.get('res.users').browse(cr,uid,uid).company_id.property_valuation_price_type.id
        pricetype=self.pool.get('product.price.type').browse(cr,uid,price_type_id)
        context['currency_id']=self.pool.get('res.users').browse(cr,uid,uid).company_id.currency_id.id
        
        if not product_ids:
            product_ids = product_obj.search(cr, uid, [])

        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_by_uom = {}
        products_by_id = {}
        for product in products:
            products_by_uom.setdefault(product.uom_id.id, [])
            products_by_uom[product.uom_id.id].append(product)
            products_by_id.setdefault(product.id, [])
            products_by_id[product.id] = product

        result = {}
        result['product'] = []
        for id in ids:
            quantity_total = 0.0
            total_price = 0.0
            for uom_id in products_by_uom.keys():
                fnc = self._product_get
                if recursive:
                    fnc = self._product_all_get
                ctx = context.copy()
                ctx['uom'] = uom_id
                qty = fnc(cr, uid, id, [x.id for x in products_by_uom[uom_id]],
                        context=ctx)
                for product_id in qty.keys():
                    if not qty[product_id]:
                        continue
                    product = products_by_id[product_id]
                    quantity_total += qty[product_id]
                    
                    # Compute based on pricetype
                    # Choose the right filed standard_price to read
                    amount_unit=product.price_get(pricetype.field, context)[product.id] 
                    price = qty[product_id] * amount_unit
                         
                    total_price += price
                    result['product'].append({
                        'price': amount_unit,
                        'prod_name': product.name,
                        'code': product.default_code, # used by lot_overview_all report!
                        'variants': product.variants or '',
                        'uom': product.uom_id.name,
                        'prod_qty': qty[product_id],
                        'price_value': price,
                    })
        result['total'] = quantity_total
        result['total_price'] = total_price
        return result
        
        def _product_get_all_report(self, cr, uid, ids, product_ids=False,
                context=None):
            return self._product_get_report(cr, uid, ids, product_ids, context,
                    recursive=True)
                    
        def _product_value(self, cr, uid, ids, field_names, arg, context={}):
            return super(stock_location, self)._product_value(cr, uid, ids, field_names, arg, context)

        _columns = {
            'stock_real_value': fields.function(_product_value, method=True, type='float', string='Real Stock Value', multi="stock"),
            'stock_virtual_value': fields.function(_product_value, method=True, type='float', string='Virtual Stock Value', multi="stock"),
        }
stock_location()

#----------------------------------------------------------
# Stock Picking
#----------------------------------------------------------
class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def _get_price_unit_invoice(self, cr, uid, move_line, type, context={}):
        '''Return the price unit for the move line'''
        if type in ('in_invoice', 'in_refund'):
            # Take the user company and pricetype
            price_type_id=self.pool.get('res.users').browse(cr,uid,uid).company_id.property_valuation_price_type.id
            pricetype=self.pool.get('product.price.type').browse(cr,uid,price_type_id)    
            context['currency_id']=self.pool.get('res.users').browse(cr,uid,uid).company_id.currency_id.id        
            amount_unit=move_line.product_id.price_get(pricetype.field, context)[move_line.product_id.id] 
            return amount_unit
        else:
            return move_line.product_id.list_price
            
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        '''Return ids of created invoices for the pickings'''
        return super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id,group,type,context)
        
stock_picking()

# ----------------------------------------------------
# Move
# ----------------------------------------------------
class stock_move(osv.osv):
    _inherit = "stock.move"

    def action_done(self, cr, uid, ids, context=None):
        track_flag = False
        for move in self.browse(cr, uid, ids):
            if move.move_dest_id.id and (move.state != 'done'):
                cr.execute('insert into stock_move_history_ids (parent_id,child_id) values (%s,%s)', (move.id, move.move_dest_id.id))
                if move.move_dest_id.state in ('waiting', 'confirmed'):
                    self.write(cr, uid, [move.move_dest_id.id], {'state': 'assigned'})
                    if move.move_dest_id.picking_id:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
                    else:
                        pass
                        # self.action_done(cr, uid, [move.move_dest_id.id])
                    if move.move_dest_id.auto_validate:
                        self.action_done(cr, uid, [move.move_dest_id.id], context=context)

            #
            # Accounting Entries
            #
            acc_src = None
            acc_dest = None
            if move.location_id.account_id:
                acc_src = move.location_id.account_id.id
            if move.location_dest_id.account_id:
                acc_dest = move.location_dest_id.account_id.id
            if acc_src or acc_dest:
                test = [('product.product', move.product_id.id)]
                if move.product_id.categ_id:
                    test.append( ('product.category', move.product_id.categ_id.id) )
                if not acc_src:
                    acc_src = move.product_id.product_tmpl_id.\
                            property_stock_account_input.id
                    if not acc_src:
                        acc_src = move.product_id.categ_id.\
                                property_stock_account_input_categ.id
                    if not acc_src:
                        raise osv.except_osv(_('Error!'),
                                _('There is no stock input account defined ' \
                                        'for this product: "%s" (id: %d)') % \
                                        (move.product_id.name,
                                            move.product_id.id,))
                if not acc_dest:
                    acc_dest = move.product_id.product_tmpl_id.\
                            property_stock_account_output.id
                    if not acc_dest:
                        acc_dest = move.product_id.categ_id.\
                                property_stock_account_output_categ.id
                    if not acc_dest:
                        raise osv.except_osv(_('Error!'),
                                _('There is no stock output account defined ' \
                                        'for this product: "%s" (id: %d)') % \
                                        (move.product_id.name,
                                            move.product_id.id,))
                if not move.product_id.categ_id.property_stock_journal.id:
                    raise osv.except_osv(_('Error!'),
                        _('There is no journal defined '\
                            'on the product category: "%s" (id: %d)') % \
                            (move.product_id.categ_id.name,
                                move.product_id.categ_id.id,))
                journal_id = move.product_id.categ_id.property_stock_journal.id
                if acc_src != acc_dest:
                    ref = move.picking_id and move.picking_id.name or False
                    product_uom_obj = self.pool.get('product.uom')
                    default_uom = move.product_id.uom_id.id
                    date = time.strftime('%Y-%m-%d')
                    q = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
                    if move.product_id.cost_method == 'average' and move.price_unit:
                        amount = q * move.price_unit
                        # Base computation on valuation price type
                    else:
                         company=move.company_id and move.company_id or self.pool.get('res.users').browse(cr,uid,uid).company_id
                         context['currency_id']=company.currency_id.id
                         pricetype=self.pool.get('product.price.type').browse(cr,uid,company.property_valuation_price_type.id)
                         amount_unit=move.product_id.price_get(pricetype.field, context)[move.product_id.id]
                         amount=amount_unit * q or 1.0
                              
                         
                    partner_id = False
                    if move.picking_id:
                        partner_id = move.picking_id.address_id and (move.picking_id.address_id.partner_id and move.picking_id.address_id.partner_id.id or False) or False
                    lines = [
                            (0, 0, {
                                'name': move.name,
                                'quantity': move.product_qty,
                                'product_id': move.product_id and move.product_id.id or False,
                                'credit': amount,
                                'account_id': acc_src,
                                'ref': ref,
                                'date': date,
                                'partner_id': partner_id}),
                            (0, 0, {
                                'name': move.name,
                                'product_id': move.product_id and move.product_id.id or False,
                                'quantity': move.product_qty,
                                'debit': amount,
                                'account_id': acc_dest,
                                'ref': ref,
                                'date': date,
                                'partner_id': partner_id})
                    ]
                    self.pool.get('account.move').create(cr, uid, {
                        'name': move.name,
                        'journal_id': journal_id,
                        'line_id': lines,
                        'ref': ref,
                    })
        self.write(cr, uid, ids, {'state': 'done', 'date_planned': time.strftime('%Y-%m-%d %H:%M:%S')})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_trigger(uid, 'stock.move', id, cr)
        return True

stock_move()


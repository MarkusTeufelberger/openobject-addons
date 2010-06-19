# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_retails module for OpenERP, allows the management of deposit

#    Copyright (C) 2009 Smile.fr. All Rights Reserved
#    authors: Raphaël Valyi, Xavier Fernandez

#    Copyright (C) 2010 SYLEAM Info Services (<http://www.syleam.fr/>) Suzanne Jean-Sebastien
#
#    This file is a part of sale_retails
#
#    sale_retails is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_retails is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields
from osv import osv

from mx import DateTime
import netsvc


class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        default.update({'payment_ids':False,})
        return super(sale_order, self).copy(cr, uid, id, default, context)
    
    def _get_customer_name(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for so in self.browse(cr, uid, ids):
            res[so.id] = so.partner_id.name
        return res
    
    def _set_customer_name(self, cr, user, id, name, value, arg, context):
        pass
    
    def _amount_paid(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for so in self.browse(cr, uid, ids):
            total = 0
            for payment in so.payment_ids:
                total += payment.debit - payment.credit
            res[so.id] = total
        return res
    
    _columns = {
                'customer_name':fields.function(_get_customer_name, type='char', fnct_inv=_set_customer_name, method=True, string='New Customer Name', size=64),
            #TODO: use it to reset the shop_id.warehouse_id used in original action_ship_create
                'amount_paid': fields.function(_amount_paid, string="Deposits", method=True, type="float"),
                'payment_ids': fields.one2many('account.move.line', 'sale_id', 'Deposits', readonly=True, states={'prevalidated':[('readonly', False)], 'progress':[('readonly', False)]}),
                'state': fields.selection([
            ('draft', 'Quotation'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'Manual In Progress'),
            ('progress', 'In Progress'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ('cancel', 'Cancel'),
            ('prevalidated', 'Prevalidated'),
            ], 'Order State', readonly=True, help="Gives the state of the quotation or sale order. The exception state is automatically set when a cancel operation occurs in the invoice validation (Invoice Exception) or in the packing list process (Shipping Exception). The 'Waiting Schedule' state is set when the invoice is confirmed but waiting for the scheduler to run on the date 'Date Ordered'.", select=True),
        }

    _defaults = {
                 }

    
    def onchange_customer_name(self, cr, uid, ids, name, context={}):
        partner_ids = self.pool.get('res.partner').search(cr, uid, [('name', 'ilike', name)])
        if len(partner_ids) > 0:
            names = self.pool.get('res.partner').read(cr, uid, partner_ids, ['name'])
            names = [i['name'] for i in names]
            names = "\n".join(names)
            return {'value':{'warning_showed': True}, 'warning': {'title':"Warning", 'message':"A partner with a similar name already exists:\n%s" % names}}
        return {}
    
    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        ctx['from_sale'] = True #used to make sure payments moves will be properly balanced
        created_id = super(sale_order, self).create(cr, uid, vals, ctx)
        return created_id

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        ctx['from_sale'] = True #used to make sure payments moves will be properly balanced
        if isinstance(ids, list):
            for id in ids:
                self.write(cr, uid, id, vals, ctx)
            return True
        else:
            return super(sale_order, self).write(cr, uid, ids, vals, ctx)
        
    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        tx = context.copy()
        ctx['from_sale'] = True #used to make sure payments moves will be properly balanced
        return super(sale_order, self).unlink(cr, uid, ids, ctx)
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        if not context:
            context = {}
        """take care of the company id, especially because the user generating the invoice might be different form the one encoding the sale order"""
        invoice_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context)
        self.pool.get('account.invoice').write(cr, uid, invoice_id, {'company_id': order.user_id.company_id.id})
        #journal selection: a bit like account.invoice._get_journal but also company aware!
        res = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', order.user_id.company_id.id)], limit=1)
        if res:
            self.pool.get('account.invoice').write(cr, uid, invoice_id, {'journal_id': res[0]}) 
        return invoice_id


    def customize_procurement(self, cr, uid, ids, *args):
        return True
    
    def post_deposits(self, cr, uid, ids, *args):
        """validate point of sale payments eventually"""
        for order in self.browse(cr, uid, ids, {}):
            if order.shop_id.deposit_validation == 'sale_confirm':
                for payment in order.payment_ids:
                    self.pool.get('account.move').post(cr, uid, [payment.move_id.id], *args)

    def action_ship_create(self, cr, uid, ids, *args):
        """Run the MRP when the order picking is created"""
        result = super(sale_order, self).action_ship_create(cr, uid, ids, *args)
        self.post_deposits(cr, uid, ids, *args)
        #self.customize_procurement(cr, uid, ids, *args)
        #cr.commit()
        #self.pool.get('mrp.procurement').run_scheduler(cr, uid, automatic=False, use_new_cursor=cr.dbname, context={})
        return result
 


sale_order()


class sale_shop(osv.osv):
    _inherit = "sale.shop"
    
    _columns = {
                    'default_deposit_percent': fields.integer("Default Deposit %", help="percentage of the deposits by default"),
                    'deposit_validation': fields.selection([('sale_confirm','Automatically once Order Confirmed'),('invoice_confirm','Automatically once Invoice is Confirmed'),('manual','Manual Validation Only')], 'Deposits Accounting Validation', required=True),
                }
    
    _defaults = {
                    'default_deposit_percent': lambda * a: 30,
                    'deposit_validation': lambda *a: 'invoice_confirm'
                 }
    
sale_shop()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

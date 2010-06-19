# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_retails module for OpenERP, allows the management of deposit
#
#    Copyright (C) 2009 Smile.fr. All Rights Reserved
#    authors: Raphaël Valyi, Xavier Fernandez
#
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
from tools.translate import _
import netsvc
import time

class simple_deposit_wizard(osv.osv_memory):
    _name = "sale_simple_pos.simple_deposit_wizard"
    
    def _set_default_amount(self, cr, uid, context={}):
        sale_order_id = context.get('active_id', False)
        if not sale_order_id:
            return 0.0
        sale_order = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        if sale_order.amount_paid > 0: #no new deposit in case of workflow reset
            return 0.0
        return (float(sale_order.shop_id.default_deposit_percent) / 100.0 or 1.0) * sale_order.amount_total
    
    def _set_amount_all(self, cr, uid, context={}):
        sale_order_id = context.get('active_id', False)
        if not sale_order_id:
            return 0.0
        sale_order = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        return sale_order.amount_total
    
    def _set_default_pay_all(self, cr, uid, context={}):
        sale_order_id = context.get('active_id', False)
        if not sale_order_id:
            return False
        else:
            sale_order = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
            return (float(sale_order.shop_id.default_deposit_percent) / 100.0) == 1.0 or False
    
    def _set_default_desc(self,cr,uid,context={}):
        sale_order_id = context.get('active_id', False)
        if not sale_order_id:
            return False
        else:
            order = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
            return 'Deposit' + " - " + order.partner_id.name
        
    def pay_all_change(self, cr, uid, ids, pay_all=False, amount_all=False):
        res = {}
        if pay_all and amount_all:
            res['value'] = {'amount_paid':amount_all}
        return res
    
    _columns = {'amount_paid': fields.float("New Deposit", required=True),
                'amount_all': fields.float("Amount All"),
                'pay_all': fields.boolean("Pay All"),
                'payment_description':fields.char('Description',size=100),
                #'payment_date': fields.date("Payment date", required=True),
                'journal_id': fields.many2one('account.journal', "Journal/Payment Mode", domain="[('type','=','cash'), ('pos_enabled','=','True')]"),
                }
    
    _defaults = {
                 #'payment_date': lambda *args: time.strftime('%Y-%m-%d'),
                 'amount_paid': _set_default_amount,
                 'amount_all': _set_amount_all,
                 'pay_all': _set_default_pay_all,
                 }
    

    def create_simple_deposit(self, cr, uid, ids, context={}):
        sale_order_id = context.get('active_id', False)
        if not sale_order_id:
            return {'type': 'ir.actions.act_window_close', }       
        order = self.pool.get('sale.order').browse(cr, uid, sale_order_id, context)
        vals = self.read(cr, uid, ids)[0]
        amount_paid = vals['amount_paid']
        if amount_paid:
            journal_id = vals['journal_id']
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            period_ids = self.pool.get('account.period').find(cr, uid, {})
            period_id = False
            if len(period_ids):
                period_id = period_ids[0]  #FIXME, ripped code from invoice.py, but does that select the appropriate period?
            self.pool.get("account.move.line").create(cr, uid, {'name':vals['payment_description'] or  _('Deposit') + " - " + str(vals['amount_paid']) + " - " + order.partner_id.name,
                                                                'journal_id': vals['journal_id'],
                                                                'account_id': journal.default_credit_account_id.id,
                                                                'ref': order.name,
                                                                'period_id': period_id,
                                                                'sale_id': sale_order_id,
                                                                'debit': vals['amount_paid'],
                                                                'date': time.strftime('%Y-%m-%d'),
                                                                'state': 'draft',
                                                                }, {'from_sale': True})

        self.pool.get('sale.order').write(cr, uid, sale_order_id, {'state': 'prevalidated'})
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', sale_order_id, 'simple_pos_simple_confirm', cr)
        return {'type': 'ir.actions.act_window_close', }


simple_deposit_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

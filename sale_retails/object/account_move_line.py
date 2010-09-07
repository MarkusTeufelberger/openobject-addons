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

class account_move_line(osv.osv):
    _inherit = "account.move.line"
    
    def unlink(self, cr, uid, ids, context=None, check=True):
        if context and context.get('from_sale', False):
            del(context['from_sale'])
            for payment in self.browse(cr, uid, ids):
                if payment.sale_id:
                    #TODO FIXME take care of company when doing payment.sale_id.partner_id.property_account_receivable.id
                    balanced_move_id = self.search(cr, uid, [('id', '!=', payment.id), ('move_id', '=', payment.move_id.id)])[0]
                    super(account_move_line, self).unlink(cr, uid, [balanced_move_id], context, check)
        return super(account_move_line, self).unlink(cr, uid, ids, context, check)

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        res = super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check)
        if context and context.get('from_sale', False):
            del(context['from_sale'])
            pay_move_id = False
            partner = False
            for payment in self.browse(cr, uid, ids):
                if payment.sale_id:
                    pay_move_id = payment.move_id.id
                    partner = payment.sale_id.partner_id
                    #TODO FIXME take care of company when doing payment.sale_id.partner_id.property_account_receivable.id
                    balanced_move_id = self.search(cr, uid, [('id', '!=', payment.id), ('move_id', '=', payment.move_id.id)])[0]
                    super(account_move_line, self).write(cr, uid, [payment.id], {'partner_id': partner.id})
                    super(account_move_line, self).write(cr, uid, [balanced_move_id], {'state': 'draft', 'partner_id': partner.id, 'sale_id': False, 'debit': payment.credit, 'credit': payment.debit, 'account_id': partner.property_account_receivable.id}, context, check, update_check)
            if payment.sale_id.state == 'progress' and payment.sale_id.shop_id.deposit_validation == 'sale_confirm':
                self.pool.get('account.move').post(cr, uid, [pay_move_id], context)
        return res

    def create(self, cr, uid, vals, context=None, check=True):
        if context and context.get('from_sale', False):
            del(context['from_sale'])
            payment_id = super(account_move_line, self).create(cr, uid, vals, context, check)
            payment = self.browse(cr, uid, payment_id)
            balanced_move_id = self.copy(cr, uid, payment_id)
            #TODO FIXME take care of company when doing payment.sale_id.partner_id.property_account_receivable.id
            self.write(cr, uid, [payment_id], {'partner_id': payment.sale_id.partner_id.id}, context)
            self.write(cr, uid, [balanced_move_id], {'state': 'draft', 'partner_id': payment.sale_id.partner_id.id, 'sale_id': False, 'debit': payment.credit, 'credit': payment.debit, 'account_id': payment.sale_id.partner_id.property_account_receivable.id}, context, check=False)
            if payment.sale_id.state == 'progress' and payment.sale_id.shop_id.deposit_validation == 'sale_confirm':
                self.pool.get('account.move').post(cr, uid, [payment.move_id.id], context)
            return payment_id
        else:
            return super(account_move_line, self).create(cr, uid, vals, context, check)
    
    def journal_id_changed(self, cr, uid, ids, journal_id=False, credit=False, debit=False, order_name=False, partner_id=False):
        res = {}
        res['value'] = {'ref': order_name}
        partner_name = ''
        if partner_id:
            partner_name = " - " +  self.pool.get('res.partner').browse(cr, uid, partner_id).name
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
        if debit > 0:
            res['value'].update({'name': 'Deposit - ' + str(debit) + partner_name})
            if journal_id:
                if not journal.default_debit_account_id:
                    raise osv.except_osv(_('Error !'), _('Your journal must have a default debit and credit account.'))
                res['value'].update({'account_id': journal.default_credit_account_id.id})
        elif credit > 0:
            res['value'].update({'name': 'Refund - ' + str(debit) + partner_name})
            if journal_id:
                if not journal.default_credit_account_id:
                    raise osv.except_osv(_('Error !'), _('Your journal must have a default debit and credit account.'))
                res['value'].update({'account_id': journal.default_debit_account_id.id})

        period_ids = self.pool.get('account.period').find(cr, uid, {})
        period_id = False
        if len(period_ids):
            period_id = period_ids[0]
        res['value'].update({'period_id': period_id}) #FIXME, ripped code from invoice.py, but does that select the appropriate period?

        return res
    
    _columns = {
                'sale_id': fields.many2one('sale.order', "Sale Order"),
              }


    def _set_default_debit(self, cr, uid, context={}):
        amount_paid = context.get('amount_paid', False)
        amount_total = context.get('amount_total', False)
        if amount_total:
            paid = amount_paid or 0
            left = amount_total - paid
            if left > 0:
                return left
            else:
                return False
        return False
    
    def _set_default_credit(self, cr, uid, context={}):
        amount_paid = context.get('amount_paid', False)
        amount_total = context.get('amount_total', False)
        if amount_total:
            paid = amount_paid or 0
            left = paid - amount_total
            if left > 0:
                return left
            else:
                return False
        return False

    
    _defaults = {
                 'credit': _set_default_credit,
                 'debit': _set_default_debit,
                 }
    
account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

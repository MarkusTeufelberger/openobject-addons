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

from osv import osv, fields
import time
from tools.translate import _

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    def line_get_convert(self, cr, uid, x, part, date, context={}):
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context)
        res['asset_method_id'] = x.get('asset_method_id', False)
        return res

    def _refund_cleanup_lines(self, cr, uid, lines):
        for line in lines:
#            raise osv.except_osv('Error !', 'method id %s %s %s %s'%line[0],line[1], line[2], line[5]) 
            if 'asset_method_id' in line:
#                raise osv.except_osv('Error !', 'method id %s'%line[asset_method_id]) 
                line['asset_method_id'] = line.get('asset_method_id', False) and line['asset_method_id'][0]
        res = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines)
        return res

    def action_move_create(self, cr, uid, ids, *args):
        res = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
        for inv in self.browse(cr, uid, ids):
            if inv.type == "out_refund":
                continue
            for line in inv.invoice_line:
                if not line.asset_method_id:
                    continue
                if line.invoice_id.type == "in_invoice":
                    type = "purchase"
                elif line.invoice_id.type == "in_refund":
                    type = "refund"
                elif line.invoice_id.type == "out_invoice":
                    type = "sale"
                method = line.asset_method_id
                if type in ["purchase","refund"]:
                    if method.state=='draft':
                        self.pool.get('account.asset.method').validate(cr, uid, [method.id])
                    elif method.state in ["depreciated","closed"]:
                        raise osv.except_osv(_('Error !'), _('You cannot assign Product "%s" to Asset Method "%s". This method is already depreciated or is inactive (sold or abandoned).')%(line.product_id.name, method.name,)) 
                    if not line.asset_method_id.asset_id.date:
                        self.pool.get('account.asset.asset').write(cr, uid, [method.asset_id.id], {
                            'date': line.invoice_id.date_invoice,
                            'partner_id': line.invoice_id.partner_id.id,
                        })
                    base = (type == 'purchase') and line.price_subtotal or - line.price_subtotal
                    expense = 0.0
                elif type == "sale":
                    if not method.account_residual_id:
                        raise osv.except_osv(_('Error !'), _('Product "%s" is assigned to Asset Method "%s". But this method has no Sale Residual Account to make asset moves.')%(line.product_id.name, method.name,)) 
                    elif line.asset_method_id.state in ["closed","draft"]:
                        raise osv.except_osv(_('Error !'), _('You cannot assign Product "%s" to Asset Method "%s". This method is in Draft state or is inactive (sold or abandoned).')%(line.product_id.name, method.name,)) 
                    direct = (method.account_asset_id.id == method.account_expense_id.id)
                    base = direct and - method.value_residual or -method.value_total
                    expense = not direct and -(method.value_total - method.value_residual) or False
                    method_obj = self.pool.get('account.asset.method')
                    method_obj._post_3lines_move(cr, uid, method= method, period=line.invoice_id.period_id, \
                            date = line.invoice_id.date_invoice, acc_third_id = method.account_residual_id.id, \
                            base = base, expense = expense,)
                    method_obj._close(cr, uid, method)
                note = _("Product name: ") + line.product_id.name + ' ['+line.product_id.code+ \
                        _("]\nInvoice date: ") + line.invoice_id.date_invoice + \
                        _("\nPrice: ") + str(line.price_subtotal)
                self.pool.get('account.asset.history')._history_line(cr, uid, type, method, line.product_id.name, base, expense, \
                            line.invoice_id, note, )
        return  res
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Asset Method', help = "Select the asset depreciation method if you wish to assign the purchase invoice line to fixed asset. If method doesn't exists yet you will have to create it and probably the asset itself too. After selecting the asset method the invoice line account should change according to the asset method settings but please check it before creating the invoice."),
    }

    def move_line_get_item(self, cr, uid, line, context={}):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context)
        res['asset_method_id'] = line.asset_method_id and line.asset_method_id.id or False
        return res

    def asset_method_id_change(self, cr, uid, ids, asset_method_id, type, context={}):
        result = {}
        if asset_method_id and type in ["in_invoice","in_refund"]:
            result['account_id'] = self.pool.get('account.asset.method').browse(cr, uid, asset_method_id,{}).account_asset_id.id
        return {'value': result}
        
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


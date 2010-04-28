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
            for line in inv.invoice_line:
                if not line.asset_method_id:
                    continue
                if line.invoice_id.type == "in_invoice":
                    type = "purchase"
                elif line.invoice_id.type == "in_refund":
                    type = "refund"
                elif line.invoice_id.type == "out_invoice":
                    type = "sale"
                if type in ["purchase","refund"]:
                    if not line.asset_method_id.asset_id.date:
                        self.pool.get('account.asset.asset').write(cr, uid, [line.asset_method_id.asset_id.id], {
                            'date': line.invoice_id.date_invoice,
                            'partner_id': line.invoice_id.partner_id.id,
                        })                    
                    if line.asset_method_id.state=='draft':
                        self.pool.get('account.asset.method').validate(cr, uid, [line.asset_method_id.id])
                elif type == "sale":
                    if not line.asset_method_id.account_residual_id:
                        raise osv.except_osv(_('Error !'), _('Product "%s" is assigned to Asset Method "%s". But this method has no Sale Residual Account to make asset moves.')%(line.product_id.name, line.asset_method_id.name,)) 
                    method_obj = self.pool.get('account.asset.method')
                    method_obj._post_3lines_move(cr, uid, method= line.asset_method_id, period=line.invoice_id.period_id, \
                            date = line.invoice_id.date_invoice, acc_third_id = line.asset_method_id.account_residual_id.id)
                    method_obj._close(cr, uid, line.asset_method_id)
                        
                self.pool.get('account.asset.history').create(cr, uid, {
                    'type': type,
                    'asset_method_id': line.asset_method_id.id,
                    'asset_id' : line.asset_method_id.asset_id.id,
#                      'name': "Buying asset",
                    'partner_id': line.invoice_id.partner_id.id,
                    'invoice_id': line.invoice_id.id,
                    'note': "Product name: " + line.product_id.name + ' ['+line.product_id.code+"]\nInvoice date: "+line.invoice_id.date_invoice,
                })
        


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


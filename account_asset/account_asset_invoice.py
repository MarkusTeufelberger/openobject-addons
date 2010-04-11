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


account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Asset Method', help = "Select the asset depreciation method if you wish to assign the purchase invoice line to fixed asset. If method doesn't exists yet you will have to create it and probably the asset itself too. After selecting the asset method the invoice line account should change according to the asset method settings but please check it before creating the invoice."),
    }

    def move_line_get_item(self, cr, uid, line, context={}):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context)
        if line.invoice_id.type == "in_invoice":
            type = "purchase"
        elif line.invoice_id.type == "in_refund":
            type = "refund"
        elif line.invoice_id.type == "out_invoice":
            type = "sale"
        if line.asset_method_id:
            res['asset_method_id'] = line.asset_method_id.id
            if not line.asset_method_id.asset_id.date:
                self.pool.get('account.asset.asset').write(cr, uid, [line.asset_method_id.asset_id.id], {
                    'date': line.invoice_id.date_invoice,
                    'partner_id': line.invoice_id.partner_id.id,
                }, context)                    
            if line.asset_method_id.state=='draft':
                self.pool.get('account.asset.method').validate(cr, uid, [line.asset_method_id.id], context)
            self.pool.get('account.asset.history').create(cr, uid, {
                'type': type,
                'asset_method_id': line.asset_method_id.id,
                'asset_id' : line.asset_method_id.asset_id.id,
#                'name': "Buying asset",
                'partner_id': line.invoice_id.partner_id.id,
                'invoice_id': line.invoice_id.id,
                'note': "Product name: " + line.product_id.name + ' ['+line.product_id.code+"]\nInvoice date: "+line.invoice_id.date_invoice,
                }, context)
        else:
            res['asset_method_id'] = False
        return res

    def asset_method_id_change(self, cr, uid, ids, asset_method_id,context={}):
        result = {}
        if asset_method_id:
            result['account_id'] = self.pool.get('account.asset.method').browse(cr, uid, asset_method_id,{}).account_asset_id.id
        return {'value': result}
        
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


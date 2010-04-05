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
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
        'asset_method_id': fields.many2one('account.asset.method', 'Asset Method', help = "Select the asset depreciation method if you wish to assign the purchase invoice line to fixed asset. If method doesn't exists yet you will have to create it and probably the asset itself too. After selecting the asset method the invoice line account should change according to the asset method settings but please check it before creating the invoice."),
    }
    def move_line_get_item(self, cr, uid, line, context={}):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context)
        res['asset_method_id'] = line.asset_method_id.id or False
        if line.asset_method_id.id and (line.asset_method_id.asset_id.state=='draft'):
            self.pool.get('account.asset.asset').validate(cr, uid, [line.asset_method_id.asset_id.id], context)
        return res

    def asset_method_id_change(self, cr, uid, ids, asset_method_id,context={}):
        result = {}
        if asset_method_id:
#            asset_method_obj = self.pool.get('account.asset.method').browse(cr, uid, asset_method_id,{}).account_asset_id.id
#            prop_id = asset_method_obj.search(cr,uid,[('asset_id','=',asset_id)])
#            method_id = prop_id[0]
#            asset_prop = asset_method_obj.browse(cr, uid, method_id,{})
            result['account_id'] = self.pool.get('account.asset.method').browse(cr, uid, asset_method_id,{}).account_asset_id.id
        return {'value': result}
        
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


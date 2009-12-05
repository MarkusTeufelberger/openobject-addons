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

class account_invoice_line(osv.osv):
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"
    _columns = {
        'cost_price': fields.float('Cost Price', digits=(16, 2)),
    }
    def write(self, cr, uid, ids, vals, context={}):
        if vals.get('product_id' , False):
            res=self.pool.get('product.product').read(cr, uid, [vals['product_id']], ['standard_price'])
            vals['cost_price']=res[0]['standard_price']
        return super(account_invoice_line, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context={}):
        if vals.get('product_id',False):
            res=self.pool.get('product.product').read(cr, uid, [vals['product_id']], ['standard_price'])
            vals['cost_price']=res[0]['standard_price']
        return super(account_invoice_line, self).create(cr, uid, vals, context)
account_invoice_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


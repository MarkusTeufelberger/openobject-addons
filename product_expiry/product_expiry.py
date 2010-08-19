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

import datetime
from osv import fields,osv
import pooler

class stock_production_lot(osv.osv):
    _name = 'stock.production.lot'
    _inherit = 'stock.production.lot'

    def _get_date(dtype):
        def calc_date(self, cr, uid, context={}):
            if context.get('product_id', False):
                product = pooler.get_pool(cr.dbname).get('product.product').browse(cr, uid, [context['product_id']])[0]
                duree = getattr(product, dtype) or 0
                date = datetime.datetime.today() + datetime.timedelta(days=duree)
                return date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return False
        return calc_date

    _columns = {
        'dlc': fields.datetime('Product usetime'),
        'dluo': fields.datetime('DLUO'),
        'removal_date': fields.datetime('Removal date'),
        'alert_date': fields.datetime('Alert date'),
    }

    _defaults = {
        'dlc': _get_date('life_time'),
        'dluo': _get_date('use_time'),
        'removal_date': _get_date('removal_time'),
        'alert_date': _get_date('alert_time'),
    }
stock_production_lot()

class product_product(osv.osv):
    _inherit = 'product.product'
    _name = 'product.product'
    _columns = {
        'life_time': fields.integer('Product lifetime', help="Product's lifetime in days."),
        'use_time': fields.integer('Product usetime', help="Product's use time in days."),
        'removal_time': fields.integer('Product removal time', help="Product's removal time in days."),
        'alert_time': fields.integer('Product alert time', help="Product's alert time in days."),
    }
product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


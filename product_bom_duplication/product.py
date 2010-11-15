# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Zikzakmedia. All Rights Reserved
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

from osv import fields, osv


class product_product(osv.osv):
    _inherit = 'product.product'
    
    def copy(self, cr, uid, id, default=None, context=None):
        """Copies the product and the BoM of the product"""
        if not context:
            context={}
        copy_id = super(product_product, self).copy(cr, uid, id, default=default, context=context)

        bom_obj = self.pool.get('mrp.bom')
        bom_ids = bom_obj.search(cr, uid, [('product_id','=',id)], context=context)
        for bom_id in bom_ids:
            bom_obj.copy(cr, uid, bom_id, {'product_id': copy_id}, context=context)
        return copy_id

product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

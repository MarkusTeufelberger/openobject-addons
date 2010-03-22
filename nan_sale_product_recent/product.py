# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


from osv import fields,osv

class product_product(osv.osv):
    _inherit = 'product.product'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context.get('sale_partner_filter') and isinstance(context['sale_partner_filter'], int):
            cr.execute( """
                SELECT DISTINCT 
                    sol.product_id 
                FROM 
                    sale_order so, 
                    sale_order_line sol 
                WHERE 
                    so.id = sol.order_id AND 
                    so.partner_id = %s
            """, (context['sale_partner_filter'],) )
            ids = [x[0] for x in cr.fetchall()]
            args = args[:]
            args.append( ('id','in', ids) )
        return super(product_product,self).search(cr, uid, args, offset, limit, order, context, count)

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

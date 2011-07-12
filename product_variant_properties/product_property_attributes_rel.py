# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

"""Many2many with attributes between property groups and product template"""

from osv import osv, fields

class product_property_attributes_rel(osv.osv):
    """Many2many with attributes between property groups and product template"""

    _name = "product.property.attributes.rel"

    _columns = {
        'property_group_id': fields.many2one('mrp.property.group', 'Property Group', required=True),
        'product_tmpl_id': fields.many2one('product.template', 'Product', required=True)
    }


product_property_attributes_rel()

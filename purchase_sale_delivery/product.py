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

"""add a new cost price with delivery cost"""

from osv import osv, fields
from tools import config

class product_template(osv.osv):
    """add a new cost price with delivery cost"""
    _inherit = 'product.template'

    _columns = {
        'standard_delivery_price': fields.float('Delivery cost price', digits=(16, 4), help="The cost of the product with a percentage of delivery cost.")
    }

    _defaults = {
        'standard_delivery_price': lambda *a: 1.0
    }

product_template()
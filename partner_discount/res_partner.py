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

"""adds new field discount on partner"""

from osv import fields,osv

class res_partner(osv.osv):
    """adds new field discount on partner"""
    _inherit = 'res.partner'

    _columns = {
        'sale_discount': fields.float("Sale Discount (%)", help="If select this partner in sale order, discount will be dragged to sale order lines"),
    }

    _defaults = {
        'sale_discount': lambda *a: 0.0
    }

res_partner()


# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
from tools.translate import _

class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'multi_partner':fields.boolean('Share Partner', help='When create Partners and Partner Addresses, they are available for all companies.'),
        'multi_product':fields.boolean('Share Product', help='When create Products, they are available for all companies.'),
    }

    _defaults = {
        'multi_partner': lambda *a: 1,
        'multi_product': lambda *a: 1,
    }

res_company()

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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

import time

class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'shipping': fields.boolean('Shipping'),
        'from_zip' : fields.char('From Zip', size=64),
        'from_city' : fields.char('From City', size=64, select=2),
        'from_country_id': fields.many2one('res.country', 'From Country'),
        'from_state_id': fields.many2one("res.country.state", 'From Fed. State', domain="[('country_id','=',from_country_id)]"),
        'to_zip' : fields.char('To Zip', size=64),
        'to_city' : fields.char('To City', size=64, select=2),
        'to_country_id': fields.many2one('res.country', 'To Country'),
        'to_state_id': fields.many2one("res.country.state", 'To Fed. State', domain="[('country_id','=',from_country_id)]"),
    }

product_template()

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright Camptocamp SA
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

from osv import fields,osv
from tools import config
from tools.translate import _
import netsvc
import time

class c2c_block_customer_sale(osv.osv):
    """c2c block customer Sale"""
    
    _inherit="res.partner"
    _columns={
            'block_sales':fields.boolean("Block This Customer Sales"),                                 
    }

c2c_block_customer_sale()    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 
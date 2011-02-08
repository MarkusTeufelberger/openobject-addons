# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Guewen Baconnier. Copyright Camptocamp SA
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

import netsvc
import time

from magentoerpconnect import magerp_osv
from osv import fields, osv
from tools.translate import _

class Product(magerp_osv.magerp_osv):
    """ Inherit product to remove the images when duplicating a media otherwise
    Magento will link the same image to the 2 products"""
    _inherit = 'product.product'

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context = {}
        if context is None:
            default = {}
            
        default['image_ids'] = False

        return super(Product, self).copy(cr, uid, id, default=default, context=context)   
           
Product()

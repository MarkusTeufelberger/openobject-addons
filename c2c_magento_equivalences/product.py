# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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

from osv import fields, osv
from tools.translate import _

class Product(osv.osv):
    " Inherit product in order to manage equivalences"
    _inherit = 'product.product'
    
    _columns = {
                    ##We choose this name in order to be sure that it will not be in attribute set. 
                   'c2c_debonix_equiv':fields.many2one('product.product','Equivalence',help='Product to use for compatibility'),
                   'c2c_debonix_compatibility':fields.many2many(
                          'product.product', 
                          'product_compatibility_rel', 
                          'product_id', 
                          'compatible_id', 
                          'Compatibility',
                          required=False
                         ),
                }
                
    def onchange_equiv(self, cursor, uid, ids, equiv_id=None, context={}):
        if not equiv_id:
            return {}
        refs = self.pool.get('external.referential').search(cursor, uid, [])
        if len(refs) > 1 :
            raise Exception(_('Equivalence does not support multi shop yet'))
        ext_id = self.oeid_to_extid(cursor, uid, equiv_id, refs[0])
        if not ext_id and equiv_id:
            raise Exception(_('The equivalence product has no equivalence on Magento, please export catalog or product before doing this'))
        self.write(cursor, uid, ids, {'x_magerp_zdbx_default_sku_secours':str(ext_id)})
        return {'x_magerp_zdbx_default_sku_secours':str(ext_id)}
Product()


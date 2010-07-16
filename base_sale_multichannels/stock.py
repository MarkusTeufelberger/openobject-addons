# -*- encoding: utf-8 -*-
#########################################################################
#                                                                       #
#########################################################################
#                                                                       #
# Copyright (C) 2010 BEAU Sébastien                                     #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields,osv
from tools.translate import _

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    def create_ext_complet_shipping(self, cr, uid, id, external_referential_id, ctx):
        osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))
        
    def create_ext_partial_shipping(self, cr, uid, id, external_referential_id, ctx):            
        osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))
        
    def add_ext_tracking_reference(self, cr, uid, id, carrier_id, ext_shipping_id, tracking_carrier_ref, ctx):
        osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))
        
    def check_ext_carrier_reference(self, cr, uid, id, carrier_id, ctx):
        #TAKE CARE THAT THE VALUE OF THE CARRIER IS OK
        #INDEED IF THE YOU HAVE A ERROR IN THE UPDATE OF THE TRACKING NUMBER FUNCTION add_ext_tracking_reference
        #OPENERP WILL STOP AFTER CREATING THE PICKING AND WON'T WRITE THE EXTERNAL ID IN ir_model_data !!  
        return False
    
    
 
stock_picking()


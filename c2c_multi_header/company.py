# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
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

import netsvc
from osv import fields, osv


def get_logo_by_name_report_helper(name):
        header_obj = self.pool.get('c2c.header_img')
        header_img_id = header_obj.search(
                                            self.cr, 
                                            self.uid, 
                                            [('name','=',name)]
                                        )
        if not header_img_id :
            return u''
        if isinstance(header_img_id, list):
            header_img_id = header_img_id[0]
        
        return header_obj.browse(self.cr, self.uid, header_img_id).img
        

class ResCompany(osv.osv):
    """override company to add product price computation"""
    
    _inherit = "res.company"
    _columns = {
                'header_image' : fields.many2many(
                                                    'c2c.header_img', 
                                                    'company_img_rel', 
                                                    'company_id', 
                                                    'img_id', 
                                                    'Available Images'
                                                ),
                'header_rml' : fields.many2many(
                                                    'c2c.header_rml', 
                                                    'company_rml_rel', 
                                                    'company_id', 
                                                    'rml_id', 
                                                    'Available RML'
                                                ),
    }   
    

ResCompany()
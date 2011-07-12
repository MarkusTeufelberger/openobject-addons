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

"""Changes about properties models"""

from osv import osv,fields

class mrp_property_group(osv.osv):
    """adds one2many field related to properties"""
    _inherit = 'mrp.property.group'

    _columns = {
        'property_ids': fields.one2many('mrp.property', 'group_id', 'Properties')
    }
    
mrp_property_group()

class mrp_property(osv.osv):
    """adds new fields"""
    _inherit = 'mrp.property'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=64),
    }

mrp_property()

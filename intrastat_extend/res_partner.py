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

"""add hs or intrastat selection for partner"""

from osv import osv, fields

class res_partner(osv.osv):
    """add hs or intrastat selection for partner"""

    _inherit = 'res.partner'

    _columns = {
        'hs_intrastat': fields.selection([('intrastat', 'Intrastat'), ('hs', 'HS')], string='Intrastat kind', help="If you select intrastat code, in reports it appears with all digits but if you select HS only was showed the first six characters of instrastat in reports.", required=True)
    }

    _defaults = {
        'hs_intrastat': lambda *a: 'intrastat'
    }

res_partner()

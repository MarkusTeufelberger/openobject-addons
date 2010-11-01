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

from osv import osv,fields

class last_packing_confirm(osv.osv_memory):
    """Last Product to Scan"""
    
    _name = 'last.packing.confirm'
    _description = __doc__

last_packing_confirm()

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
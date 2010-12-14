# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

class mgmtsystem_procedure(osv.osv):
    """
    Procedure of the management system
    """
    _name = "mgmtsystem.procedure"
    _description = "Procedure of the management system"
    _columns = {
        'id': fields.integer('ID', readonly=True),
        'name': fields.char('Procedure', size=50, required=True),
        'objective': fields.text('Objective'),
        'domain': fields.text('Application Domain'),
        'responsibilities': fields.text('Responsibilities')
    }

mgmtsystem_procedure()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

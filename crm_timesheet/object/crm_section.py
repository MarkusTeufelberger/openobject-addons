# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2008-2009 Syleam (<http://syleam.fr>). All Rights Reserved
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

from osv import osv
from osv import fields

class crm_section_analytic_account(osv.osv):
    """Add default analytic account to crm case section"""
    _inherit = 'crm.case.section'

    _columns = {
        'account_id' : fields.many2one('account.analytic.account', 'Analytic Account', 
                ondelete='cascade', select=True, help='If account is empty, it must defined on partner'),
        'req_partner': fields.boolean('Account required on partner', 
                help='Analytic accound is required on partner form'),
        'calculate_duration': fields.boolean('Calculate Duration ?',
                help="Calculate duration from timesheet to duration's field.",),
    }

crm_section_analytic_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

class res_partner_crm_analytic(osv.osv):
    """
    Define one analytic account by section,
    to disable the analytic account for a section, add line with section and
    not fill the analytic account
    """
    _name = 'res.partner.crm.analytic'
    _description = 'CRM Partner Analytic Account'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'section_id': fields.many2one('crm.case.section', 'Section', required=True),
        'account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete='cascade'),
    }

res_partner_crm_analytic()

class res_partner(osv.osv):
    """
    Add a new tab on partner, to select the analytic account by section
    """
    _inherit = 'res.partner'

    _columns = {
        'crm_analytic_ids': fields.one2many('res.partner.crm.analytic', 'partner_id', 'CRM Analytic Account'),
    }

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

from osv import fields, osv

class account_fiscal_position_rule(osv.osv):
    _name = "account.fiscal.position.rule"
    _columns = {
	'name': fields.char('Name', size=64, required=True),
	'description': fields.char('Description', size=128),
	'from_country': fields.many2one('res.country','Country Form'),
	'from_state': fields.many2one('res.country.state', 'State To'),
	'to_country': fields.many2one('res.country', 'Country Form'),
	'to_state': fields.many2one('res.country.state', 'State To'),
	'fiscal_postition_id': fields.many2one('account.fiscal.position.template', 'Fiscal Postion'),
        'use_sale' : fields.boolean('Use in sales order'),
	'use_invoice' : fields.boolean('Use in Invoices'),
    }
account_fiscal_position_rule()

# -*- encoding: utf-8 -*-
#########################################################################
#
#    Copyright (C) 2010 Anevia
#    Author : Sébastien Beau <sebastien.beau@akretion.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from osv import osv,fields



class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'coface_ref': fields.char('Coface Reference', size=9, help="assurance customer reference code"),
        'credit_limit': fields.float(string='Credit Limit', readyonly=1),
        'coface_identifier_type_1': fields.char('Legal Identifier Type 1', size=32),
        'coface_identifier_type_2': fields.char('Legal Identifier Type 2', size=32),
        'coface_identifier_type_3': fields.char('Legal Identifier Type 3', size=32),
        'coface_identifier_1': fields.char('Legal Identifier 1', size=32),
        'coface_identifier_2': fields.char('Legal Identifier 2', size=32),
        'coface_identifier_3': fields.char('Legal Identifier 3', size=32),
        'coface_credit_history_ids': fields.one2many('coface.credit.history', 'partner_id', 'Credit History'),
    }
    
res_partner()




class coface_credit_history(osv.osv):
    _name = "coface.credit.history"
    _description = 'coface credit amount and insurance history'
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade'),
        'coface_product': fields.char('Coverage Category', size=32, required=1),
        'coface_rating': fields.char('Coface Rating', size=6),
        'coface_amount_requested': fields.float('Amount Requested'),
        'coface_request_date': fields.date('Request Date'),
        'coface_credit_limit': fields.float('Credit Limit', required=1),
        'coface_status': fields.char('Insurance Status', size=32),
        'coface_status_details': fields.char('Status Details', size=255),
        'coface_status_date': fields.date('Status Date'),
        }

coface_credit_history()

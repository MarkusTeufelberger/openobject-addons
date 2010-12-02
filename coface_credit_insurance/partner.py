# -*- encoding: utf-8 -*-
#########################################################################
#
#    Copyright (C) 2010 Anevia
#    Author : Sébastien Beau <sebastien.beau@akretion.com.br>
#    Author : Alexis de Lattre <alexis.delattre@akretion.com>
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
        'coface_identifier': fields.char('Coface EASY number', size=16, help="EASY number of the partner"),
        'coface_country': fields.char('Partner country', size=32, help="Country of the partner, imported from Coface database."),
        'credit_limit': fields.float(string='Credit Limit', readyonly=1), # readyonly=1 ????
        'coface_identifier_type_1': fields.char('Legal identifier type 1', size=32),
        'coface_identifier_type_2': fields.char('Legal identifier type 2', size=32),
        'coface_identifier_type_3': fields.char('Legal identifier type 3', size=32),
        'coface_identifier_1': fields.char('Legal identifier 1', size=32),
        'coface_identifier_2': fields.char('Legal identifier 2', size=32),
        'coface_identifier_3': fields.char('Legal identifier 3', size=32),
        'coface_credit_history_ids': fields.one2many('coface.credit.history', 'partner_id', 'Credit History'),
    }
    
res_partner()




class coface_credit_history(osv.osv):
    _name = "coface.credit.history"
    _description = 'coface credit amount and insurance history'
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade'),
        'coface_product': fields.char('Coface product', size=32, required=1, help="Coface insurance product, for example : Agrément, Accord Express, Garantie @rating, ..."),
        'coface_rating': fields.char('Coface rating', size=6, help="Coface rating. Possible values : X, R, NR, @, @@, @@@. Empty in case of 'Agrément'."),
        'coface_requested_amount': fields.integer('Requested amount', help="In case of 'Agrément', contains the coverage amount that we requested. Empty if not an 'Agrément'."),
        'coface_requested_amount_cur': fields.char('Requested amount currency', size=3, help="Currency of the requested amount. Should always be 'EUR'."), # we should point to res_currency ??
        'coface_request_date': fields.date('Request date', help="Date of the coverage request."),
        'coface_credit_limit': fields.integer('Credit limit', help="This is the answer of Coface to our request : the amount of the coverage. This is the important field !"),
        'coface_credit_limit_cur': fields.char('Credit limit currency', size=3, help="Currency of the credit limit. Should always be 'EUR'."),
        'coface_decision_status': fields.char('Decision status', size=20, help="Status of Coface's decision."),
        'coface_decision_type': fields.char('Decision type', size=128, help="Type of Coface's decision."),
        'coface_decision_details': fields.text('Decision details', help="Details about Coface's decision. Usually gives the reason why Coface refused the coverage."),
        'coface_decision_date': fields.date('Decision date', help="Coface's decision takes effect from that date."),
        }

coface_credit_history()

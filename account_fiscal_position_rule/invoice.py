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

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False):
        
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, partner_id,date_invoice, payment_term, partner_bank_id)

        if not partner_id:
            return result

        if result['value']['fiscal_position']:
            return result

        #Use the current user to get the company_id
        user_partner_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id

        company_addr = self.pool.get('res.partner').address_get(cr, uid, [user_partner_id.id], ['default'])
        company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
        
        from_country = company_addr_default.country_id.id
        from_state = company_addr_default.state_id.id
        
        partner_invoice_addr = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['invoice'])
        partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [partner_invoice_addr['invoice']])[0]
        
        to_country = partner_addr_default.country_id.id
        to_state = partner_addr_default.state_id.id
        
        fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, [('from_country','=',from_country),('from_state','=',from_state),('to_country','=',to_country),('to_state','=',to_state),('use_invoice','=',True)])
        if fsc_pos_id: 
            result['value']['fiscal_position'] = fsc_pos_id[0]
        
        return result
        
account_invoice()
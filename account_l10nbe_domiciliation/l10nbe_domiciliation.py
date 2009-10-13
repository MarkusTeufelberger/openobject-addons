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
    _description = 'Account Invoice'
    _columns = {
        'domiciled' : fields.boolean('Domiciled'), 
        'domiciled_send_date' : fields.date('Domiciliation Sending Date'), 
        }
    
    def on_change_partner_id(self, cr, uid, id, partner):
        if not partner:
            return {'value' : {'domiciled' : False}}
        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner)
        domiciled = partner_obj.domiciliation_bool
        return {'value' : {'domiciled' : domiciled} }

account_invoice()

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _description = 'Partner'
    _columns = {
        'domiciliation_bool':fields.boolean('Domiciliation'), 
        'domiciliation' : fields.char('Domiciliation Number', size=32)
        }
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


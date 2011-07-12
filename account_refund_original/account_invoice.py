# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Luis Manuel Angueira Blanco$
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

"""
AEAT 349 model object and detail lines.
"""

from osv import osv, fields


class account_invoice(osv.osv):
    """
    Inheritance of account invoce to add some fields
    """
    _inherit = 'account.invoice'

    _columns = {
        'refund_invoices_description' : fields.text('Refund invoices description'),
        'origin_invoices_ids' : fields.many2many('account.invoice', 'account_invoice_refunds_rel', 'refund_invoice_id', 'original_invoice_id', 'Refund invoice',
            help='Links to original invoice which is referred by current refund invoice')
    }

    def refund(self, cr, uid, ids, date=None, period_id=None, description=None):
        """fill automatically refund-invoice relationship fields"""

        new_ids = super(account_invoice, self).refund(cr, uid, ids, date=date, period_id=period_id, description=description)

        if new_ids:
            self.write(cr, uid, new_ids[0], {
                            'origin_invoices_ids': [(6, 0, ids)],
                            'refund_invoices_description': description or ''})

        return new_ids
    
account_invoice()


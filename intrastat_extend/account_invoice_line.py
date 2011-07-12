# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
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

"""add instrastat code to invoice lines"""

from osv import osv, fields

class account_invoice_line(osv.osv):
    """add instrastat code to invoice lines"""

    _inherit = 'account.invoice.line'

    _columns = {
        'intrastat_id': fields.related('product_id', 'intrastat_id', type='many2one', relation='report.intrastat.code', string='Intrastat', readonly=True)
    }

account_invoice_line()

class account_invoice(osv.osv):
    """inherit create refund invoice function to map new fields"""

    _inherit = 'account.invoice'

    def _refund_cleanup_lines(self, cr, uid, lines):
        """maps intratat fielsds in the ugly function to map all fields of account.invoice.line when creates refund invoice"""
        res = super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines)
        for line in res:
            if 'intrastat_id' in line[2]:
                line[2]['intrastat_id'] = line[2].get('intrastat_id', False) and line[2]['intrastat_id'][0]

        return res


account_invoice()

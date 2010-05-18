# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import time
import tools
from datetime import datetime
from osv import osv
from osv import fields
from tools.translate import _

class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def _balance(self, cr, uid, ids, field_name, arg, context):
        if not ids:
            return {}

        result = {}
        ids = ','.join( [str(int(x)) for x in ids] )

        cr.execute("SELECT aml.id, aml.account_id, aml.partner_id, aml.date, am.name, aml.debit, aml.credit FROM account_move_line aml, account_move am WHERE aml.move_id = am.id AND aml.id IN (%s)" % ids)
        for record in cr.fetchall():
            cr.execute("""
                SELECT 
                    SUM(debit-credit) 
                FROM 
                    account_move_line aml,
                    account_move am
                WHERE 
                    aml.move_id = am.id AND
                    aml.account_id=%s AND 
                    aml.partner_id=%s AND
                    (
                        aml.date<%s OR 
                        (aml.date=%s AND aml.name<=%s AND am.name <> '/') OR 
                        (aml.date=%s AND aml.id<=%s AND am.name = '/') 
                    )
            """, (record[1],record[2],record[3],record[3],record[4],record[3],record[0]))
            balance = cr.fetchone()[0] or 0.0
            # Add/substract current debit and credit
            balance += record[5] - record[6]
            result[record[0]] = balance
        return result

    _columns = {
        'balance': fields.function(_balance, method=True, string='Balance'),
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}

        ids = super(account_move_line,self).search(cr, uid, args, offset, limit, order, context, count)

        if context.get('statement_of_accounts') and ids:
            # If it's a statement_of_accounts, ignore order given
            ids = ','.join( [str(int(x)) for x in ids] )
            cr.execute("SELECT aml.id FROM account_move_line aml, account_move am WHERE aml.move_id = am.id AND aml.id IN (%s) ORDER BY aml.date ASC, am.name" % ids)
            result = cr.fetchall()
            ids = [x[0] for x in result]
        return ids

account_move_line()

class account_statement_accounts_wizard(osv.osv_memory):
    _name = 'account.statement.accounts.wizard'

    _columns = {
        'account_id': fields.many2one('account.account', 'Account', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
    }

    def action_cancel(self, cr, uid, ids, context=None):
        return {}

    def action_open(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context)

        domain = [('account_id', '=', data.account_id.id)]
        if data.partner_id:
            domain += [('partner_id', '=', data.partner_id.id)]

        model_data_ids = self.pool.get('ir.model.data').search(cr,uid, [
            ('model','=','ir.ui.view'),
            ('name','=','account_move_line_statement_of_accounts_view'),
            ('module','=','nan_account_statement_of_accounts'),
        ], context=context)
        resource_id = self.pool.get('ir.model.data').read(cr, uid, model_data_ids, ['res_id'], context)[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(resource_id,'tree'),(False,'form')],
            'context': "{'statement_of_accounts': True}",
            'domain': domain,
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
        }

account_statement_accounts_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


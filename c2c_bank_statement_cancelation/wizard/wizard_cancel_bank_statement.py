# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Vincent Renaville
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

import wizard
import pooler

INFOFORM = '''<?xml version="1.0"?>
<form string="Cancel Bank Statement">
    <separator string="Cancel Bank Statement" colspan="4"/>
    <image name="gtk-dialog-info" colspan="2"/>
    <label string="You will cancel the Bank Statement and reset it to draft,\
                  It will unreconciled all move and reset them to draft also"\
                  colspan="2"/>
</form>'''

def _trans_unrec(cursor, uid, data):
    '''
    this will function will unreconciled all moveline linked with a bank statement
    '''
    pool = pooler.get_pool(cursor.dbname)
    recs = pool.get('account.move.line').read(
                            cursor,
                            uid,
                            data,
                            ['reconcile_id', 'reconcile_partial_id', 'move_id']
                            )
    unlink_ids = []
    full_recs = filter(lambda x: x['reconcile_id'], recs)
    rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
    
    part_recs = filter(lambda x: x['reconcile_partial_id'], recs)
    part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]

    moves = filter(lambda x: x['move_id'], recs)
    moves_ids = [rec['move_id'][0] for rec in moves]

    unlink_ids += rec_ids
    unlink_ids += part_rec_ids

    if len(unlink_ids):
        pool.get('account.move.reconcile').unlink(cursor, uid, unlink_ids)
    if len(moves_ids):
        pool.get('account.move').button_cancel(cursor, uid, moves_ids)


def _trans_cancel(self, cursor, uid, data, context):
    '''
    this will function will call all function to cancel
    a bank statement.
    - Unreconcile all account_move_line
    - Set to draft all move linked unreconciled account_move_line
    - Set to draft account_bank_statement
    '''
    pool = pooler.get_pool(cursor.dbname)
    recs = pool.get('account.bank.statement').browse(cursor, uid, data['ids'])
    for bank_statement in recs:
        if bank_statement.state != 'confirm':
            raise wizard.except_wizard('Error !', 'This bank Statement is\
                                       not confirmed, so needless to cancel it')
        # Get the Id of the bank statement
        recs_move_line_ids = pool.get('account.move.line').search(
            cursor, uid, [
                ('statement_id', '=', bank_statement.id)
                ]
            )
        _trans_unrec(cursor, uid, recs_move_line_ids)
        pool.get('account.bank.statement').button_cancel(
                cursor, uid, [bank_statement.id]
                )
    return {}

class WizBankStatementCancel(wizard.interface):
    '''
    Wizard to cancel a bank statement in one click
    '''
    states = {
        'init': {
            'actions': [],
            'result': {
                    'type': 'form',
                    'arch': INFOFORM,
                    'fields': {},
                    'state':
                        [('end', 'Cancel'),('unrec', 'Cancel Bank Statement')]
                    }
        },
        'unrec': {
            'actions': [_trans_cancel],
            'result': {'type': 'state', 'state':'end'}
        }
    }
WizBankStatementCancel('account.bank.statement.cancelation')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


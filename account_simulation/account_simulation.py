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

class account_journal_simulation(osv.osv):
    _name = "account.journal.simulation"
    _description = "Simulation level"
    _columns = {
        'name': fields.char('Simulation name', size=32, required=True),
        'code': fields.char('Simulation code', size=8, required=True),
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the simulation must be unique !')
    ]
    _order = "name"
account_journal_simulation()

def _state_simul_get(self, cr, uid, context={}):
    obj = self.pool.get('account.journal.simulation')
    ids = obj.search(cr, uid, [])
    res = obj.read(cr, uid, ids, ['code', 'name'], context)
    return [('valid','Base')]+ [(r['code'], r['name']) for r in res]

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'state': fields.selection(_state_simul_get, 'Status', required=True),
        'parent_ids': fields.many2many('account.journal', 'account_journal_simulation_rel', 'journal_src_id', 'journal_dest_id', 'Childs journal'),
        'child_ids': fields.many2many('account.journal', 'account_journal_simulation_rel', 'journal_dest_id', 'journal_src_id', 'Parent journal'),
    }
    _defaults = {
        'state': lambda self,cr,uid,context: 'valid'
    }
account_journal()

class account_move_line(osv.osv):
    _inherit = "account.move.line"
    def search_not_run(self, cr, uid, crit, offset=0, limit=None, order=None, context={}):
        if not 'fiscalyear' in context:
            context['fiscalyear'] = self.pool.get('account.fiscalyear').find(cr, uid)
        ok = True
        for c in crit:
            if c[0]=='journal_id':
                ok = False
                break
        if 'journal_id' in context:
            ok=False
        if ok:
            plus = ''
            for state in context.get('journal_state', []):
                plus+=",'"+state+"'"
            cr.execute("select id from account_journal where state in ('valid'"+plus+")")
            crit.append(('journal_id', 'in', map(lambda x: x[0], cr.fetchall())))
        res = super(account_move_line, self).search(cr, uid, crit, offset, limit, order, context)
        return res

    def _query_get(self, cr, uid, obj='l', context={}):
        res = super(account_move_line, self)._query_get(cr, uid, obj, context)
        if context.get('journal_state', []):
            plus = " and ("+obj+".journal_id in (select id from account_journal where state in ('valid', "+','.join(map(lambda x: "'"+x+"'", context['journal_state']))+")))"
        else:
            plus = " and ("+obj+".journal_id in (select id from account_journal where state='valid'))"
        return res+plus
account_move_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


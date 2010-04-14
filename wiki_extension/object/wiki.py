# -*- coding: utf-8 -*-
##############################################################################
#
#    wiki_extension module for OpenERP, Add new field for tax include in product
#    Copyright (C) 2009 SYLEAM Info Services (<http://www.Syleam.fr/>) Sebastien LANGE
#
#    This file is a part of wiki_extension
#
#    wiki_extension is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wiki_extension is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _

AVAILABLE_STATES = [
    ('open', _('Running')),
    ('done', _('Read Only')),
    ('cancel', _('Obsolete')),
]

class WikiGroup(osv.osv):
    _inherit = "wiki.groups"
    _columns={
        'member_ids': fields.many2many('res.users', 'wiki_groups_user_rel', 'wiki_groups_id', 'uid', 'Wiki Groups Members',
            help="Wiki groups's member. Not used in any computation, just for information purpose."),
    }
WikiGroup()


class Wiki(osv.osv):
    _inherit="wiki.wiki"
    _columns={
        'text_area':fields.text("Content", select=False),
        'state': fields.selection(AVAILABLE_STATES, 'Status', size=16),
    }

    def _default_group(self, cr, uid, context={}):
        if 'group_id' in context and context['group_id']:
            return context['group_id']
        return False

    _defaults = {
        'group_id' : _default_group,
        'state': lambda *a: 'open',
    }
Wiki()

class History(osv.osv):
    _inherit="wiki.wiki.history"
    _columns={
      'text_area':fields.text("Text area",select=False),
    }
History()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny - NaN  (http://www.nan-tic.com) All Rights Reserved.
#
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
from tools.translate import _

_form = """<?xml version="1.0"?>
<form string="Merge Wizard" col="2">
	<label string="This process will merge all selected production orders into one." colspan="2"/>
	<label string="" colspan="2"/>
	<label string="Note that merging is only possible between orders that produce the same product using the same production process." colspan="2"/>
</form>
"""


class mrp_production_merge(wizard.interface):
    def _merge(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        ids = data.get('ids')
        if not ids or len(ids) <= 1:
            raise wizard.except_wizard(_('Error !'), _('You must select at least two production orders!'))
        new_production_id = pool.get('mrp.production')._merge(cr, uid, ids, context)
        return {
            'domain': "[('id','=',%d)]" % new_production_id,
            'name': _('Production Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }

    states = {
        'init' : {
            'actions' : [],
            'result' : {
                'type' : 'form',
                'arch' : _form,
                'fields' : {},
                'state' : [('end', 'Cancel', 'gtk-cancel'), ('merge', 'Merge', 'gtk-ok') ]
            }
        },
        'merge' : {
            'actions' : [],
            'result' : {
                'type' : 'action',
                'action': _merge,
                'state' : 'end'
            }
    },
    }
mrp_production_merge("mrp.production.merge")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

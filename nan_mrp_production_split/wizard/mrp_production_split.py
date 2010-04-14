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
<form string="Split Wizard" col="2">
	<label string="This process will split selected production order into two." colspan="2"/>
	<label string="" colspan="2"/>
	<label string="Please specify the quantity you want to leave in the current production order." colspan="2"/>
    <field name="quantity"/>
</form>
"""


class mrp_production_split(wizard.interface):
    def _split(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        id = data.get('id')
        if not id:
            raise wizard.except_wizard(_('Error !'), _('You must select at least one production order!'))
        quantity = data['form']['quantity']
        if not quantity or quantity <= 0:
            raise wizard.except_wizard(_('Error !'), _('You must specify a value greater than 0.'))
        productions = pool.get('mrp.production')._split(cr, uid, id, quantity, context)
        return {
            'domain': "[('id','in',%s)]" % productions,
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
                'fields' : {'quantity': {'string': 'Quantity', 'type': 'float'} },
                'state' : [('end', 'Cancel', 'gtk-cancel'), ('split', 'Split', 'gtk-ok') ]
            }
        },
        'split' : {
            'actions' : [],
            'result' : {
                'type' : 'action',
                'action': _split,
                'state' : 'end'
            }
    },
    }
mrp_production_split("mrp.production.split")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright Camptocamp SA
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
import wizard
import pooler
from osv import osv
from tools.translate import _

class wiz_non_confirmed_order_open(wizard.interface):
    
    def _open_waiting_sale_order(self, cr, uid, data, context):
        
        """Open Non Confirm Sale order"""
        
        pool = pooler.get_pool(cr.dbname)
        partner_obj = pool.get('res.partner')
        sale_obj = pool.get('sale.order')
        partner_ids = partner_obj.search(cr, uid, [('block_sales', '=', True)])
        if not len(partner_ids):
            raise wizard.except_wizard(_('Warning!'), _('Not Any Partner are blocked !'))
        partner = partner_obj.browse(cr, uid, partner_ids)
        ids = sale_obj.search(cr, uid, [('partner_id', 'in', partner_ids),('state','=','draft')])
        
        domain = "[('id','in',["+','.join(map(str,ids))+"])]"
    
        value = {
            'domain': domain,
            'name': 'Sales Orders',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        return value

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type':'action', 'action':_open_waiting_sale_order, 'state':'end'}
        }
    }
wiz_non_confirmed_order_open('c2c_block_customer_sale.non.confirmed.order')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


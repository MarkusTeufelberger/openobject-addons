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

from osv import fields, osv
import netsvc
from tools.translate import _
import time

class customer_credit_warning(osv.osv_memory):
    """Customer credit warning"""
   
    _name="customer.credit.warning"
    _description = __doc__
    
    CREDIT_LIMIT_KO = _("The chosen  customer has reach his credit limit of ")
    CREDIT_LIMIT_OK = _("The current Sale Order has been confirmed ! Packing and procurement has been generated.")
    
    def default_get(self, cr, uid, fields, context=None):
        record_id = context and context.get('active_id', False) or False
        value = {}
        partner_obj = self.pool.get('res.partner') 
        for sale in self.pool.get('sale.order').browse(cr, uid, context.get('active_ids', [])):
            res_partner = partner_obj.search(cr, uid, [('id', '=', sale.partner_id.id)])
            partner = partner_obj.browse(cr, uid, res_partner)[0]
            
            if partner.block_sales == True:
                raise osv.except_osv(_('Warning'), _("The chosen customer is blocked and it is forbidden to record a sale order for him."))
                  
            moveline_obj = self.pool.get('account.move.line')
            movelines = moveline_obj.search(cr, uid, [('partner_id', '=', partner.id),('account_id.type', 'in', ['receivable', 'payable']), ('state', '<>', 'draft'), ('reconcile_id', '=', False)])
            movelines = moveline_obj.browse(cr, uid, movelines)
            
            debit, credit = 0.0, 0.0
            for line in movelines:
                if line.date_maturity < time.strftime('%Y-%m-%d'):
                    credit += line.debit
                    debit += line.credit
            if partner.credit_limit != 0.0  and (credit - debit + sale.amount_total) > partner.credit_limit:
                data_obj = self.pool.get('ir.model.data')
                data_id = data_obj._get_id(cr, uid, 'c2c_block_customer_sale', 'view_customer_credit_warning')
                view_id = False
                if data_id:
                    view_id = data_obj.browse(cr, uid, data_id).res_id
                    value =  {            
                        'name': _('Warning'), 
                        'view_type': 'form', 
                        'view_mode': 'form', 
                        'res_model': 'customer.credit.warning', 
                        'view_id': False, 
                        'views': [(view_id, 'form')], 
                        'type': 'ir.actions.act_window', 
                        'target': 'new', 
                        'nodestroy': True
                    }
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', context.get('active_id', False), 'order_confirm', cr)
        return value

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        """override fields_view_get method"""
        
        result = super(customer_credit_warning, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar=toolbar)
        partner_obj = self.pool.get('res.partner') 
        default =self.default_get(cr, uid, fields=False, context=context)
        for sale in self.pool.get('sale.order').browse(cr, uid, context.get('active_ids', [])):
            xml = '''<?xml version="1.0"?>\n<form string="Warning" >\n\t''' 
            if default=={}:
                xml += '''<label string="%s"/>\n''' % (self.CREDIT_LIMIT_OK)
            else:
                res_partner = partner_obj.search(cr, uid, [('id', '=', sale.partner_id.id)])
                partner = partner_obj.browse(cr, uid, res_partner)[0]
                xml += '''<label string="%s %s"/>\n''' % (self.CREDIT_LIMIT_KO,partner.credit_limit)
                
            xml += '''<separator colspan="4"/>'''
            xml += '''<group col="2" colspan="4">
                                 <button icon='gtk-ok' special="cancel"
                                     string="_Ok" />
                             </group>'''
            xml += '''</form>'''
        result['arch'] = xml
        return result
    
customer_credit_warning()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
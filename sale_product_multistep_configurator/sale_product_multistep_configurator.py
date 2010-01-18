# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2009 Smile.fr. All Rights Reserved
#    authors: Raphaël Valyi, Xavier Fernandez
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

class sale_product_multistep_configurator_configurator_step(osv.osv):
    _name = "sale_product_multistep_configurator.configurator.step"
    _columns = {
                'name': fields.char('Value Name', size=64, select=1), #TODO related?
                'model_id': fields.many2one('ir.model', 'Object ID', required=True, select=True),
                'sequence' : fields.integer('Sequence', help="Determine in which order step are executed"),
                }
    _order = 'sequence'
    
    def update_context_before_step(self, cr, user, context={}):
        """Hook to allow a configurator step module to update the context before running, for instance to skip this step."""
        return context
    
    def next_step(self, cr, user, context={}):
        context = self.update_context_before_step(cr, user, context)
        index = context.get('next_step', 0)
        context.update({'next_step': index+1 })
        model_list= context.get('step_list', False)
        if index and model_list and index < len(model_list):
            return {
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': model_list[index],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'context': context,
                }
        else:
            if context.get('active_id_object_type', False) == 'sale.order.line':
                return {
                        'type': 'ir.actions.act_window_close',
                    }
            else:
                
                #fake the product_id_change event occuring when manually selecting the product
                uid = user
                order_line = self.pool.get('sale.order.line').browse(cr, uid, context.get('sol_id', False), {})
                sale_order = order_line.order_id
                pricelist = sale_order.pricelist_id.id
                date_order = sale_order.date_order
                fiscal_position = sale_order.fiscal_position.id
                qty_uos = order_line.product_uos_qty
                uos = order_line.product_uos.id
                partner_id = sale_order.partner_id.id
                packaging = order_line.product_packaging.id
                product = order_line.product_id.id
                qty = order_line.product_uom_qty
                uom = order_line.product_uom.id
                qty_uos = order_line.product_uos_qty
                uos = order_line.product_uos.id
                name = order_line.name
                lang = context.get('lang', False)
                update_tax = True
                flag = True #TODO sure?
                
                
                on_change_result = self.pool.get('sale.order.line').product_id_change(cr, uid, [order_line.id], pricelist, product, qty,
                    uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag)
                
                on_change_result['value']['tax_id'] = [(6, 0, on_change_result['value']['tax_id'])] #deal with many2many and sucking geek Tiny API
                self.pool.get('sale.order.line').write(cr, uid, [order_line.id], on_change_result['value'])
                
                return {
                        'view_type': 'form',
                        "view_mode": 'form',
                        'res_model': 'sale.order.line',
                        'type': 'ir.actions.act_window',
                        'target':'new',
                        'res_id': context.get('sol_id', False),
                        'buttons': True,
                        'context': context,
                    }        

    
sale_product_multistep_configurator_configurator_step()


class ir_actions_act_window(osv.osv):
    _inherit = 'ir.actions.act_window'

    def read(self, cr, uid, ids, fields=None, context={}, load='_classic_read'):

        if isinstance(ids, (int, long)):
            read_ids = [ids]
        else:
            read_ids = ids
         
        result = super(ir_actions_act_window, self).read(cr, uid, read_ids, ['context'], context, load)[0]

        try:
            if eval(result['context']).get('multistep_wizard_dispatch', False):
                configurator_context = eval(result['context'])
                
                list_of_step_ids = self.pool.get('sale_product_multistep_configurator.configurator.step').search(cr, uid, [])
                list_of_steps = self.pool.get('sale_product_multistep_configurator.configurator.step').read(cr, uid, list_of_step_ids)
                model_names = [i['model_id'][1] for i in list_of_steps]
                action_id = self.search(cr, uid, [('res_model', '=', model_names[0])])[0]
                
                result = super(ir_actions_act_window, self).read(cr, uid, action_id, fields, context, load)
                configurator_context.update(eval(result['context']))#used to pass active_id_object_type and make sure we will dispatch here again eventually, see corresponding act_window      
                configurator_context.update({'next_step':1})#TODO have a back system + TODO be dynamic here
                configurator_context.update({'step_list': model_names})
                result['context'] = unicode(configurator_context)
                return result
            else:
                return super(ir_actions_act_window, self).read(cr, uid, ids, fields, context, load)
        except Exception, e:
            return super(ir_actions_act_window, self).read(cr, uid, ids, fields, context, load)

ir_actions_act_window()

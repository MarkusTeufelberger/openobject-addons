# -*- encoding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2009  Raphaël Valyi                                     #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import osv, fields
from base_external_referentials import external_osv
from sets import Set
import netsvc
from tools.translate import _
#from datetime import datetime
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class external_shop_group(external_osv.external_osv):
    _name = 'external.shop.group'
    _description = 'External Referential Shop Group'
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'referential_id': fields.many2one('external.referential', 'Referential', select=True, ondelete='cascade'),
        'shop_ids': fields.one2many('sale.shop', 'shop_group_id', 'Sale Shops'),
    }
    
external_shop_group()


class external_referential(osv.osv):
    _inherit = 'external.referential'
    
    _columns = {
        'shop_group_ids': fields.one2many('external.shop.group', 'referential_id', 'Sub Entities'),
    }

external_referential()


class product_category(osv.osv):
    _inherit = "product.category"
    
    def collect_children(self, category, children=None):
        if children is None:
            children = []

        for child in category.child_id:
            children.append(child.id)
            self.collect_children(child, children)

        return children
    
    def _get_recursive_children_ids(self, cr, uid, ids, name, args, context=None):
        res = {}
        for category in self.browse(cr, uid, ids):
            res[category.id] = self.collect_children(category, [category.id])
        return res

    _columns = {
        'recursive_childen_ids': fields.function(_get_recursive_children_ids, method=True, type='one2many', relation="product.category", string='All Child Categories'),
    }
    
product_category()


class sale_shop(external_osv.external_osv):
    _inherit = "sale.shop"

    def _get_exportable_product_ids(self, cr, uid, ids, name, args, context=None):
        res = {}
        for shop in self.browse(cr, uid, ids, context=context):
            root_categories = [category for category in shop.exportable_root_category_ids]
            all_categories = []
            for category in root_categories:
                all_categories += [category.id for category in category.recursive_childen_ids]

            # If product_m2mcategories module is installed search in main category and extra categories. If not, only in main category
            cr.execute('select * from ir_module_module where name=%s and state=%s', ('product_m2mcategories','installed'))
            if cr.fetchone():
                product_ids = self.pool.get("product.product").search(cr, uid, ['|',('categ_id', 'in', all_categories),('categ_ids', 'in', all_categories)])
            else:
                product_ids = self.pool.get("product.product").search(cr, uid, [('categ_id', 'in', all_categories)])
            res[shop.id] = product_ids
        return res

    _columns = {
        #'exportable_category_ids': fields.function(_get_exportable_category_ids, method=True, type='one2many', relation="product.category", string='Exportable Categories'),
        'exportable_root_category_ids': fields.many2many('product.category', 'shop_category_rel', 'categ_id', 'shop_id', 'Exportable Root Categories'),
        'exportable_product_ids': fields.function(_get_exportable_product_ids, method=True, type='one2many', relation="product.product", string='Exportable Products'),
        'shop_group_id': fields.many2one('external.shop.group', 'Shop Group', ondelete='cascade'),
        'last_inventory_export_date': fields.datetime('Last Inventory Export Time'),
        'last_images_export_date': fields.datetime('Last Images Export Time'),
        'last_update_order_export_date' : fields.datetime('Last Order Update  Time'),
        'last_products_export_date' : fields.datetime('Last Product Export  Time'),
        'referential_id': fields.related('shop_group_id', 'referential_id', type='many2one', relation='external.referential', string='External Referential'),
        'is_tax_included': fields.boolean('Prices Include Tax?', help="Requires sale_tax_include module to be installed"),
        
        #TODO all the following settings are deprecated and replaced by the finer grained base.sale.payment.type settings!
        'picking_policy': fields.selection([('direct', 'Partial Delivery'), ('one', 'Complete Delivery')],
                                           'Packing Policy', help="""If you don't have enough stock available to deliver all at once, do you accept partial shipments or not?"""),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice on Order After Delivery'),
            ('picking', 'Invoice from the Packing'),
        ], 'Shipping Policy', help="""The Shipping Policy is used to synchronise invoice and delivery operations.
  - The 'Pay before delivery' choice will first generate the invoice and then generate the packing order after the payment of this invoice.
  - The 'Shipping & Manual Invoice' will create the packing order directly and wait for the user to manually click on the 'Invoice' button to generate the draft invoice.
  - The 'Invoice on Order After Delivery' choice will generate the draft invoice based on sale order after all packing lists have been finished.
  - The 'Invoice from the packing' choice is used to create an invoice during the packing process."""),
        'invoice_quantity': fields.selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on', help="The sale order will automatically create the invoice proposition (draft invoice). Ordered and delivered quantities may not be the same. You have to choose if you invoice based on ordered or shipped quantities. If the product is a service, shipped quantities means hours spent on the associated tasks."),
        'invoice_generation_policy': fields.selection([('none', 'None'), ('draft', 'Draft'), ('valid', 'Validated')], 'Invoice Generation Policy', help="Should orders create an invoice after import?"),
        'picking_generation_policy': fields.selection([('none', 'None'), ('draft', 'Draft'), ('valid', 'Validated')], 'Picking Generation Policy', help="Should orders create a picking after import?"),
        'sale_journal': fields.many2one('account.journal', 'Sale Journal'),
    }
    
    _defaults = {
        'payment_default_id': lambda * a: 1, #required field that would cause trouble if not set when importing
        'picking_policy': lambda * a: 'direct',
        'order_policy': lambda * a: 'manual',
        'invoice_quantity': lambda * a: 'order',
        'invoice_generation_policy': lambda * a: 'draft',
        'picking_generation_policy': lambda * a: 'draft',
    }

    def _get_pricelist(self, cr, uid, shop):
        if shop.pricelist_id:
            return shop.pricelist_id.id
        else:
            return self.pool.get('product.pricelist').search(cr, uid, [('type', '=', 'sale'), ('active', '=', True)])[0]
    
    def export_categories(self, cr, uid, shop, context=None):
        if context is None:
            context = {}
        categories = Set([])
        categ_ids = []
        for category in shop.exportable_root_category_ids:
            categ_ids = self.pool.get('product.category')._get_recursive_children_ids(cr, uid, [category.id], "", [], context)[category.id]
            for categ_id in categ_ids:
                categories.add(categ_id)
        context['shop_id'] = shop.id
        self.pool.get('product.category').ext_export(cr, uid, [categ_id for categ_id in categories], [shop.referential_id.id], {}, context)
       
    def export_products_collection(self, cr, uid, shop, products, context):
        self.pool.get('product.product').ext_export(cr, uid, [product.id for product in shop.exportable_product_ids] , [shop.referential_id.id], {}, context)

    def export_products(self, cr, uid, shop, context):
        self.export_products_collection(cr, uid, shop, shop.exportable_product_ids, context)
    
    def export_catalog(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for shop in self.browse(cr, uid, ids):
            context['shop_id'] = shop.id
            context['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
            self.export_categories(cr, uid, shop, context)
            self.export_products(cr, uid, shop, context)
            shop.write({'last_products_export_date' : time.strftime('%Y-%m-%d %H:%M:%S')})
        self.export_inventory(cr, uid, ids, context)
        return False
            
    def export_inventory(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for shop in self.browse(cr, uid, ids):
            context['shop_id'] = shop.id
            context['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
            product_ids = [product.id for product in shop.exportable_product_ids]
            if shop.last_inventory_export_date:
                # we do not exclude canceled moves because it means some stock levels could have increased since last export
                recent_move_ids = self.pool.get('stock.move').search(cr, uid, [('date_planned', '>', shop.last_inventory_export_date), ('product_id', 'in', product_ids), ('state', '!=', 'draft')])
            else:
                recent_move_ids = self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', product_ids)])
            product_ids = [move.product_id.id for move in self.pool.get('stock.move').browse(cr, uid, recent_move_ids) if move.product_id.state != 'obsolete']
            product_ids = [x for x in set(product_ids)]
            res = self.pool.get('product.product').export_inventory(cr, uid, product_ids, '', context)
            shop.write({'last_inventory_export_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return res
    
    def import_catalog(self, cr, uid, ids, context):
        #TODO import categories, then products
        raise osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))
        
    def import_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for shop in self.browse(cr, uid, ids):
            context['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
            defaults = {
                            'pricelist_id':self._get_pricelist(cr, uid, shop),
                            'shop_id': shop.id,
                            'picking_policy': shop.picking_policy,
                            'order_policy': shop.order_policy,
                            'invoice_quantity': shop.invoice_quantity
                        }
            if self.pool.get('ir.model.fields').search(cr, uid, [('name', '=', 'company_id'), ('model', '=', 'sale.shop')]): #OpenERP v6 needs a company_id field on the sale order but v5 doesn't have it, same for shop...
                if not shop.company_id.id:
                    raise osv.except_osv(_('Warning!'), _('You have to set a company for this OpenERP sale shop!'))
                defaults.update({'company_id': shop.company_id.id})

            if shop.is_tax_included:
                defaults.update({'price_type': 'tax_included'})

            defaults.update(self.pool.get('sale.order').onchange_shop_id(cr, uid, ids, shop.id)['value'])

            self.import_shop_orders(cr, uid, shop, defaults, context)
        return False
            
    def import_shop_orders(self, cr, uid, shop, defaults, context):
        raise osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))

    def update_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        logger = netsvc.Logger()
        for shop in self.browse(cr, uid, ids):
            context['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)
            #get all orders, which the state is not draft and the date of modification is superior to the last update, to exports 
            req = "select ir_model_data.res_id, ir_model_data.name from sale_order inner join ir_model_data on sale_order.id = ir_model_data.res_id where ir_model_data.model='sale.order' and sale_order.shop_id=%s and ir_model_data.external_referential_id NOTNULL and sale_order.state != 'draft'"
            param = (shop.id,)

            if shop.last_update_order_export_date:
                req += "and sale_order.write_date > %s" 
                param = (shop.id, shop.last_update_order_export_date)

            cr.execute(req, param)
            results = cr.fetchall()

            for result in results:
                ids = self.pool.get('sale.order').search(cr, uid, [('id', '=', result[0])])
                if ids:
                    id = ids[0]
                    order = self.pool.get('sale.order').browse(cr, uid, id, context)            
                    order_ext_id = result[1].split('sale_order/')[1]
                    self.update_shop_orders(cr, uid, order, order_ext_id, context)
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Successfully updated order with OpenERP id %s and ext id %s in external sale system" % (id, order_ext_id))
            self.pool.get('sale.shop').write(cr, uid, shop.id, {'last_update_order_export_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return False
        
    def update_shop_orders(self, cr, uid, order, ext_id, context):
        raise osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))

    def export_shipping(self, cr, uid, ids, context):
        logger = netsvc.Logger()
        for shop in self.browse(cr, uid, ids):
            context['conn_obj'] = self.external_connection(cr, uid, shop.referential_id)        
        
            cr.execute("""
                select stock_picking.id, sale_order.id, count(pickings.id) from stock_picking
                left join sale_order on sale_order.id = stock_picking.sale_id
                left join stock_picking as pickings on sale_order.id = pickings.sale_id
                left join ir_model_data on stock_picking.id = ir_model_data.res_id and ir_model_data.model='stock.picking'
                where shop_id = %s and ir_model_data.res_id ISNULL and stock_picking.state = 'done'
                Group By stock_picking.id, sale_order.id
                """, (shop.id,))
            results = cr.fetchall()
            for result in results:
                if result[2] == 1:
                    picking_type = 'complete'
                else:
                    picking_type = 'partial'
                
                ext_shipping_id = self.pool.get('stock.picking').create_ext_shipping(cr, uid, result[0], picking_type, shop.referential_id.id, context)

                if ext_shipping_id:
                    ir_model_data_vals = {
                        'name': "stock_picking/" + str(ext_shipping_id),
                        'model': "stock.picking",
                        'res_id': result[0],
                        'external_referential_id': shop.referential_id.id,
                        'module': 'extref.' + shop.referential_id.name
                      }
                    self.pool.get('ir.model.data').create(cr, uid, ir_model_data_vals)
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Successfully creating shipping with OpenERP id %s and ext id %s in external sale system" % (result[0], ext_shipping_id))

sale_shop()


class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
                'ext_payment_method': fields.char('External Payment Method', size=32, help = "Spree, Magento, Oscommerce... Payment Method"),
                'need_to_update': fields.boolean('Need To Update')
    }
    _defaults = {
        'need_to_update': lambda *a: False,
    }

    def payment_code_to_payment_settings(self, cr, uid, payment_code, context=None):
        pay_type_obj = self.pool.get('base.sale.payment.type')
        payment_setting_ids = pay_type_obj.search(cr, uid, [['name', 'like', payment_code]])
        payment_setting_id = False
        for type in pay_type_obj.read(cr, uid, payment_setting_ids, fields=['name'], context=context):
            if payment_code in [x.strip() for x in type['name'].split(';')]:
                payment_setting_id = type['id']
        return payment_setting_id and pay_type_obj.browse(cr, uid, payment_setting_id, context) or False

    def generate_payment_with_pay_code(self, cr, uid, payment_code, partner_id, amount, payment_ref, entry_name, date, paid, context):
        payment_settings = self.payment_code_to_payment_settings(cr, uid, payment_code, context)
        if payment_settings and payment_settings.journal_id and (payment_settings.check_if_paid and paid or not payment_settings.check_if_paid):
            return self.generate_payment_with_journal(cr, uid, payment_settings.journal_id.id, partner_id, amount, payment_ref, entry_name, date, payment_settings.validate_payment, context)
        return False
        
    def generate_payment_with_journal(self, cr, uid, journal_id, partner_id, amount, payment_ref, entry_name, date, should_validate, context):
        statement_vals = {
                            'name': 'ST_' + entry_name,
                            'journal_id': journal_id,
                            'balance_start': 0,
                            'balance_end_real': amount,
                            'date' : date
                        }
        statement_id = self.pool.get('account.bank.statement').create(cr, uid, statement_vals, context)
        statement = self.pool.get('account.bank.statement').browse(cr, uid, statement_id, context)
        account_id = self.pool.get('account.bank.statement.line').onchange_partner_id(cr, uid, [], partner_id, "customer", statement.currency.id, context)['value']['account_id']
        statement_line_vals = {
                                'statement_id': statement_id,
                                'name': entry_name,
                                'ref': payment_ref,
                                'amount': amount,
                                'partner_id': partner_id,
                                'account_id': account_id,
                                'date' : date,
                               }
        statement_line_id = self.pool.get('account.bank.statement.line').create(cr, uid, statement_line_vals, context)
        if should_validate:
            self.pool.get('account.bank.statement').button_confirm(cr, uid, [statement_id], context)
        return statement_line_id


    def oe_status(self, cr, uid, order_id, paid = True, context = None):
        logger = netsvc.Logger()
        wf_service = netsvc.LocalService("workflow")
        order = self.browse(cr, uid, order_id, context)
        payment_settings = self.payment_code_to_payment_settings(cr, uid, order.ext_payment_method, context)

        if payment_settings:
            if payment_settings.payment_term_id:
                self.write(cr, uid, order.id, {'payment_term': payment_settings.payment_term_id.id})

            if payment_settings.check_if_paid and not paid:
                if order.state == 'draft' and datetime.strptime(order.date_order, '%Y-%m-%d') < datetime.now() - relativedelta(days=payment_settings.days_before_order_cancel or 30):
                    wf_service.trg_validate(uid, 'sale.order', order.id, 'cancel', cr)
                    self.write(cr, uid, order.id, {'need_to_update': False})
                    #TODO eventually call a trigger to cancel the order in the external system too
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "order %s canceled in OpenERP because older than % days and still not confirmed" % (order.id, payment_settings.days_before_order_cancel or 30))
                else:
                    self.write(cr, uid, order.id, {'need_to_update': True})
            else:
                if payment_settings.validate_order:
                    wf_service.trg_validate(uid, 'sale.order', order.id, 'order_confirm', cr)
                    
                    if order.order_policy == 'prepaid':
                        if payment_settings.validate_invoice:
                            for invoice in order.invoice_ids:
                                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
        
                    if order.order_policy == 'manual':
                        if payment_settings.create_invoice:
                            wf_service.trg_validate(uid, 'sale.order', order_id, 'manual_invoice', cr)
                            for invoice in self.browse(cr, uid, order_id).invoice_ids:
                                if payment_settings.validate_invoice:
                                    wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
        
                    # IF postpaid DO NOTHING
        
                    if order.order_policy == 'picking':
                        if payment_settings.create_invoice:
                           invoice_id = self.pool.get('stock.picking').action_invoice_create(cr, uid, [picking.id for picking in order.picking_ids])
                           if payment_settings.validate_invoice:
                               wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)

        return True
    
    def _make_invoice(self, cr, uid, order, lines, context={}):
        inv_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context)
        if order.shop_id.sale_journal:
            self.pool.get('account.invoice').write(cr, uid, [inv_id], {'journal_id' : order.shop_id.sale_journal.id}, context=context)
        return inv_id
        

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception']):
        inv_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService("workflow")
        res = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states)
        
        for order in self.browse(cr, uid, ids):
            payment_settings = self.payment_code_to_payment_settings(cr, uid, order.ext_payment_method)
            if payment_settings and payment_settings.invoice_date_is_order_date:
                inv_obj.write(cr, uid, [inv.id for inv in order.invoice_ids], {'date_invoice' : order.date_order})
            if order.order_policy == 'postpaid':
                if payment_settings and payment_settings.validate_invoice:
                    for invoice in order.invoice_ids:
                        wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
        return res




sale_order()

class base_sale_payment_type(osv.osv):
    _name = "base.sale.payment.type"
    _description = "Base Sale Payment Type"

    _columns = {
        'name': fields.char('Payment Codes', help="List of Payment Codes separated by ;", size=256, required=True),
        'journal_id': fields.many2one('account.journal','Payment Journal'),
        'picking_policy': fields.selection([('direct', 'Partial Delivery'), ('one', 'Complete Delivery')], 'Packing Policy'),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice on Order After Delivery'),
            ('picking', 'Invoice from the Packing'),
        ], 'Shipping Policy'),
        'invoice_quantity': fields.selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on'),
        'is_auto_reconcile': fields.boolean('Auto-reconcile?', help="if true will try to reconcile the order payment statement and the open invoice"),
        'validate_order': fields.boolean('Validate Order?'),
        'validate_payment': fields.boolean('Validate Payment?'),
        'create_invoice': fields.boolean('Create Invoice?'),
        'validate_invoice': fields.boolean('Validate Invoice?'),
        'check_if_paid': fields.boolean('Check if Paid?'),
        'days_before_order_cancel': fields.integer('Days Delay before Cancel', help='number of days before an unpaid order will be cancelled at next status update from Magento'),
        'invoice_date_is_order_date' : fields.boolean('Force Invoice Date?', help="If it's check the invoice date will be the same as the order date"),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term'),
    }
    
    _defaults = {
        'picking_policy': lambda *a: 'direct',
        'order_policy': lambda *a: 'manual',
        'invoice_quantity': lambda *a: 'order',
        'is_auto_reconcile': lambda *a: False,
        'validate_payment': lambda *a: False,
        'validate_invoice': lambda *a: False,
    }

base_sale_payment_type()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

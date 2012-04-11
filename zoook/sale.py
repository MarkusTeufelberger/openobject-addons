# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
#                       Jesus Martín <jmartin@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from datetime import datetime
from tools.translate import _

import netsvc
import time
import tools
import pooler
import threading

LOGGER = netsvc.Logger()

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    
    _columns = {
        'zoook_shop': fields.boolean('OpenERP e-Sale'),
        'zoook_automatic_export': fields.boolean('Automatic Export'),
        'vat_country_ids': fields.many2many('res.country','sale_shop_country_rel', 'sale_shop_id','country_id','Country'),
        'zoook_ip': fields.char('IP', size=255),
        'zoook_port': fields.char('Port', size=64),
        'zoook_username': fields.char('Username', size=255),
        'zoook_password': fields.char('Password', size=255),
        'zoook_key': fields.boolean('Ssh key'),
        'zoook_ssh_key': fields.char('Ssh Key', size=255, help='Path ssh key localhost'),
        'zoook_basepath': fields.char('Base path', size=255, help='Path of Django App. Ex: /var/www/zoook'),
        'zoook_root_category_id': fields.many2one('product.category', 'Root product Category'),
        'zoook_last_export_products': fields.datetime('Last Export Products', help='If you publish new products related another products and this products are not available in your e-sale, you need two exports (first publish products and after related products)'),
        'zoook_last_export_categories': fields.datetime('Last Export Categories'),
        'zoook_last_export_images': fields.datetime('Last Export Images'),
        'zoook_delivery_ids': fields.many2many('delivery.carrier','sale_shop_delivery_rel', 'sale_shop_id','delivery_id','Delivery'),
        'zoook_payment_types': fields.one2many('zoook.sale.shop.payment.type', 'shop_id', 'Payment Type'),
        'zoook_langs': fields.many2many('res.lang','zoook_lang_rel', 'sale_shop_id','lang_id','Languages'),
        'email_sale_order': fields.many2one('poweremail.templates', 'Email Sale Order', help='Email Template Sale Order'),
        'zoook_tax_include': fields.boolean('Taxes included',help='Show B2B price list with taxes included'),
    }

    _defaults = {
        'zoook_tax_include':lambda * a:True,
    }

    def test_connection(self, cr, uid, ids, context):
        """
        Test connection OpenERP -> Django
        """
        
        res = {}

        for sale in self.browse(cr, uid, ids):
            values = {
                'ip': sale.zoook_ip,
                'port': sale.zoook_port,
                'username': sale.zoook_username,
                'password': sale.zoook_password,
                'key': sale.zoook_key,
                'ssh_key': sale.zoook_ssh_key,
                'basepath': sale.zoook_basepath,
            }
            context['command'] = 'sync/test.py'
            test = self.pool.get('django.connect').ssh_command(cr, uid, sale.id, values, context)

            if test == 'success':
                LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Connection to server is successfull.")
                raise osv.except_osv(_('Ok!'), _('Connection to server are successfully.'))
                return True
            else:
                LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_ERROR, "Error connection to server.")
                raise osv.except_osv(_('Error!'), _('Error connection to server.'))
                return False

    def zoook_sale_shop_langs(self, cr, uid, ids):
        """
        Get ids langs available sale shop
        :ids list
        return dict sale.shop: list id langs
        """
        
        langs =  {}
        for sale in self.browse(cr, uid, ids):
            l = []
            for lang in sale.zoook_langs:
                l.append(lang.id)
            langs[str(sale.id)] = l

        return langs

    def zoook_export_conf(self, cr, uid, ids, context=None):
        """
        Global Configuration
        Execute external command (sync)
        """

        res = {}

        for sale in self.browse(cr, uid, ids):
            values = {
                'ip': sale.zoook_ip,
                'port': sale.zoook_port,
                'username': sale.zoook_username,
                'password': sale.zoook_password,
                'key': sale.zoook_key,
                'ssh_key': sale.zoook_ssh_key,
                'basepath': sale.zoook_basepath,
            }
            context['command'] = 'sync/oerp.py'
            conf = self.pool.get('django.connect').ssh_command(cr, uid, sale.id, values, context)

            if conf:
                LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Conf Export Running.")
                return True
            else:
                LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_ERROR, "Error connection to server.")
                return False

    def dj_export_countries(self, cr, uid, ids, context=None):
        """
        Return list countries IDs
        """

        for shop in self.browse(cr, uid, ids):
            countries = []

            for sale in self.browse(cr, uid, ids):
                for country in sale.vat_country_ids:
                    countries.append(country.id)

        return countries

    def dj_export_states(self, cr, uid, country_id, context=None):
        """
        Return list states IDs
        """

        states = []
        if country_id:
            states = self.pool.get('res.country.state').search(cr, uid, [('country_id','=',country_id)])

        return states

    def zoook_export_products(self, cr, uid, ids, context=None):
        """ 
        Sync Products. Sale Shop
        Execute external command (sync)
        """

        res = {}

        for sale in self.browse(cr, uid, ids):
            values = {
                'ip': sale.zoook_ip,
                'port': sale.zoook_port,
                'username': sale.zoook_username,
                'password': sale.zoook_password,
                'key': sale.zoook_key,
                'ssh_key': sale.zoook_ssh_key,
                'basepath': sale.zoook_basepath,
            }
            context['command'] = 'sync/product.py'

            thread1 = threading.Thread(target=self.zoook_export_products_thread, args=(cr.dbname, uid, sale.id, values, context))
            thread1.start()

        return True

    def zoook_export_products_thread(self, db_name, uid, sale, values, context=None):
        """Thread Export Products
        :sale: Sale Shop ID (int)
        :values: Dicc
        :context: Dicc
        return True/False
        """
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()

        product = self.pool.get('django.connect').ssh_command(cr, uid, sale, values, context)

        cr.commit()
        cr.close()

        if product:
            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Product Export Running.")
            return True
        else:
            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_ERROR, "Error connection to server.")
            return False

    def dj_export_products(self, cr, uid, ids, prods=[], context=None):
        """
        @param ids: Sale Shop IDs
        @param prods: Product Template IDS
        Return list with dicc product.template ID and list product.product IDs
        [{'product_product': [8,9], 'product_template': 7}, {'product_product': [1], 'product_template': 1}]
        """

        product_obj = self.pool.get('product.product')
        product_template_obj = self.pool.get('product.template')

        products_shop = []
        if len(prods)>0: #sync products by wizard
            for template in prods:
                template_id = int(template)
                products = product_obj.search(cr, uid, [('product_tmpl_id','=',template_id)])
                product_product = []
                for product in product_obj.browse(cr, uid, products):
                    product_product.append(product.id)
                products_shop.append({'product_template':template_id,'product_product':product_product})
        else: #sync products by cront
            for shop in self.browse(cr, uid, ids):
                last_exported_time = shop.zoook_last_export_products
                product_tmps = product_template_obj.search(cr, uid, [('zoook_exportable','=',True),('zoook_saleshop_ids','in',shop.id)])
            
                for product_tmp in product_template_obj.perm_read(cr, uid, product_tmps):
                    prods = False
                    # product.template create/modify > date exported last time
                    if last_exported_time < product_tmp['create_date'][:19] or (product_tmp['write_date'] and last_exported_time < product_tmp['write_date'][:19]):
                        prods = True
        
                    # product.product create/modify > date exported last time
                    products = product_obj.search(cr, uid, [('product_tmpl_id','=',product_tmp['id'])])
                    
                    product_product = []
                    for product in product_obj.perm_read(cr, uid, products):
                        if last_exported_time < product['create_date'][:19] or (product['write_date'] and last_exported_time < product['write_date'][:19]):
                            prods = True
                            product_product.append(product['id'])

                    if prods:
                        products_shop.append({'product_template':product_tmp['id'],'product_product':product_product})

            self.write(cr, uid, [shop.id], {'zoook_last_export_products': time.strftime('%Y-%m-%d %H:%M:%S')})

            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Products: %s" % (products_shop) )

        return products_shop

    def zoook_export_categories(self, cr, uid, ids, context=None):
        """
        Sync Categories. Sale Shop
        Execute external command (sync)
        """

        res = {}

        for sale in self.browse(cr, uid, ids):
            values = {
                'ip': sale.zoook_ip,
                'port': sale.zoook_port,
                'username': sale.zoook_username,
                'password': sale.zoook_password,
                'key': sale.zoook_key,
                'ssh_key': sale.zoook_ssh_key,
                'basepath': sale.zoook_basepath,
            }
            context['command'] = 'sync/category.py'

            thread1 = threading.Thread(target=self.zoook_export_categories_thread, args=(cr.dbname, uid, sale.id, values, context))
            thread1.start()

        return True

    def zoook_export_categories_thread(self, db_name, uid, sale, values, context=None):
        """Thread Export Categories
        :sale: Sale Shop ID (int)
        :values: Dicc
        :context: Dicc
        return True/False
        """
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()

        category = self.pool.get('django.connect').ssh_command(cr, uid, sale, values, context)

        cr.commit()
        cr.close()

        if category:
            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Category Export Running.")
            return True
        else:
            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_ERROR, "Error connection to server.")
            return False

    def dj_export_categories(self, cr, uid, ids, context=None):
        """
        Return list category IDs
        """

        for shop in self.browse(cr, uid, ids):
            categories = []
            categ_ids = []
            last_exported_time = shop.zoook_last_export_categories
            categ_ids = self.pool.get('product.category')._get_recursive_cat_children_ids(cr, uid, [shop.zoook_root_category_id.id], "", [], context)[shop.zoook_root_category_id.id]

            for categ in self.pool.get('product.category').perm_read(cr, uid, categ_ids):
                if last_exported_time < categ['create_date'][:19] or (categ['write_date'] and last_exported_time < categ['write_date'][:19]):
                    categories.append(categ['id'])

            self.write(cr, uid, [shop.id], {'zoook_last_export_categories': time.strftime('%Y-%m-%d %H:%M:%S')})

            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Categories: %s" % (categories) )

        return categories

    def zoook_export_images(self, cr, uid, ids, context=None):
        """
        Sync Images. Sale Shop
        Execute external command (sync)
        """

        res = {}

        for sale in self.browse(cr, uid, ids):
            values = {
                'ip': sale.zoook_ip,
                'port': sale.zoook_port,
                'username': sale.zoook_username,
                'password': sale.zoook_password,
                'key': sale.zoook_key,
                'ssh_key': sale.zoook_ssh_key,
                'basepath': sale.zoook_basepath,
            }
            context['command'] = 'sync/image.py'

            thread1 = threading.Thread(target=self.zoook_export_images_thread, args=(cr.dbname, uid, sale.id, values, context))
            thread1.start()
            
        return True

    def zoook_export_images_thread(self, db_name, uid, sale, values, context=None):
        """Thread Export Images
        :sale: Sale Shop ID (int)
        :values: Dicc
        :context: Dicc
        return True/False
        """
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()

        image = self.pool.get('django.connect').ssh_command(cr, uid, sale, values, context)

        cr.commit()
        cr.close()

        if image:
            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Image Export Running.")
            return True
        else:
            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_ERROR, "Error connection to server.")
            return False

    def dj_export_images(self, cr, uid, ids, context=None):
        """
        Return list images IDs
        """

        for shop in self.browse(cr, uid, ids):
            images = []
            image_ids = []
            last_exported_time = shop.zoook_last_export_images

            product_tmps = self.pool.get('product.template').search(cr, uid, [('zoook_exportable','=',True),('zoook_saleshop_ids','in',shop.id)])
            products = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id','in',product_tmps)])

            image_ids = self.pool.get('product.images').search(cr, uid, [('product_id','in',products)])

            for image in self.pool.get('product.images').perm_read(cr, uid, image_ids):
                if last_exported_time < image['create_date'][:19] or (image['write_date'] and last_exported_time < image['write_date'][:19]):
                    images.append(image['id'])

            LOGGER.notifyChannel('ZoooK Connection', netsvc.LOG_INFO, "Images: %s" % (images) )

            self.write(cr, uid, [shop.id], {'zoook_last_export_images': time.strftime('%Y-%m-%d %H:%M:%S')})

        return images

    def _zoook_sale_shop(self, cr, uid, callback, context=None):
        """
        Sale Shop Schedules
        """
        if context is None:
            context = {}

        ids = self.pool.get('sale.shop').search(cr, uid, [('zoook_shop', '=', True),('zoook_automatic_export', '=', True)], context=context)

        if ids:
            callback(cr, uid, ids, context=context)

        tools.debug(callback)
        tools.debug(ids)
        return True

    def run_zoook_export_categories(self, cr, uid, context=None):
        """
        Schedules def: Export Categories
        """
        self._zoook_sale_shop(cr, uid, self.zoook_export_categories, context=context)

    def run_zoook_export_catalog(self, cr, uid, context=None):
        """
        Schedules def: Export Catalog
        """
        self._zoook_sale_shop(cr, uid, self.zoook_export_catalog, context=context)

    def run_zoook_export_images(self, cr, uid, context=None):
        """
        Schedules def: Export Images
        """
        self._zoook_sale_shop(cr, uid, self.zoook_export_images, context=context)

sale_shop()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'payment_state': fields.selection([
         ('cancel', 'Cancel'),
         ('draft', 'Draft'),
         ('checking', 'Checking'),
         ('done', 'Done'),
        ], 'Payment State', readonly=True),
     }

    _defaults = {
        'payment_state': 'draft',
    }

    def delivery_cost(self, cr, uid, order_id, context=None):
        """Get Delivery Cost"""

        if context is None:
            context = {}
        delivery = []
        order_obj = self.pool.get('sale.order')
        grid_obj = self.pool.get('delivery.grid')
        carrier_obj = self.pool.get('delivery.carrier')

        order = order_obj.browse(cr, uid, order_id)

        carriers = order.shop_id.zoook_delivery_ids #carriers from sale shop
        if not len(carriers)>0:
            return delivery

        for carrier in carriers:
            if not carrier.active:
                continue
            grid_id = carrier_obj.grid_get(cr, uid, [carrier.id], order.partner_shipping_id.id)
            if grid_id:
                grid = grid_obj.browse(cr, uid, grid_id, context=context)
                cost = grid_obj.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context)
                delivery.append({'name':grid.carrier_id.name, 'code':grid.carrier_id.code, 'cost':cost})
        #order asc cost
        delivery.sort(key=lambda x: x['cost'], reverse = 'cost' == 'desc')

        return delivery

    def action_cancel(self, cr, uid, ids, context=None):
        """ Rewrite Payment State where cancel"""

        for o in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [o.id], {'payment_state': 'cancel'})
        return super(sale_order, self).action_cancel(cr, uid, ids, context)

    def action_cancel_draft(self, cr, uid, ids, *args):
        """ Rewrite Payment State where draft"""

        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'payment_state': 'draft'})
        return super(sale_order, self).action_cancel_draft(cr, uid, ids, *args)

    def action_wait(self, cr, uid, ids, *args):
        """ Rewrite Payment State where done"""

        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'payment_state': 'done'})
        return super(sale_order, self).action_wait(cr, uid, ids, args)

    def sale_order_payment(self, cr, uid, order, app_payment):
        """
        Sets order_policy, picking_policy, invoice_quantity depending on the payment method
         - order: Reference Order
         - app_payment: Code Payment App
        """

        if not app_payment:
            return False

        order = self.pool.get('sale.order').search(cr, uid, [('name','=',order)])
        if not len(order)>0:
            return False
        order = self.pool.get('sale.order').browse(cr, uid, order[0])

        sale_shop_payment = self.pool.get('zoook.sale.shop.payment.type').search(cr, uid, [('shop_id','=',order.shop_id.id),('app_payment','=',app_payment)])
        if not len(sale_shop_payment)>0:
            return False

        wf_service = netsvc.LocalService("workflow")
        shop_pay = self.pool.get('zoook.sale.shop.payment.type').browse(cr, uid, sale_shop_payment[0])

        values = {}
        values['order_policy'] = shop_pay.order_policy
        values['picking_policy'] = shop_pay.picking_policy
        values['invoice_quantity'] = shop_pay.invoice_quantity

        order_id = self.write(cr, uid, [order.id], values)
        
        LOGGER.notifyChannel("Sale Order", netsvc.LOG_INFO,_("Order Payment: %s") % (order.name))

        # change status sale order
        if shop_pay.confirm:
            LOGGER.notifyChannel("Sale Order", netsvc.LOG_INFO,_("Order %s change status: Done") % (order.name))
            wf_service.trg_validate(uid, 'sale.order', order.id, 'order_confirm', cr)

        return True

    def sale_order_payment_cancel(self, cr, uid, order):
        """
        Cancel Sale Order Webservices
        """

        try:
            LOGGER.notifyChannel("Sale Order", netsvc.LOG_INFO,_("Order %s change status: Cancel") % (order))
            netsvc.LocalService("workflow").trg_validate(uid, 'sale.order', order, 'cancel', cr)
            return True
        except:
            return False

sale_order()

class zoook_sale_shop_payment_type(osv.osv):
    _name = "zoook.sale.shop.payment.type"

    _description = "Zoook Sale Shop Payment Type"
    _rec_name = "payment_type_id"
 
    _columns = {
        'payment_type_id': fields.many2one('payment.type','Payment Type', required=True),
        'shop_id': fields.many2one('sale.shop','Shop', required=True),
        'picking_policy': fields.selection([('direct', 'Partial Delivery'), ('one', 'Complete Delivery')], 'Packing Policy', required=True),
        'order_policy': fields.selection([
         ('prepaid', 'Payment Before Delivery'),
         ('manual', 'Shipping & Manual Invoice'),
         ('postpaid', 'Invoice on Order After Delivery'),
         ('picking', 'Invoice from the Packing'),
        ], 'Shipping Policy', required=True),
        'invoice_quantity': fields.selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on', required=True),
        'app_payment': fields.char('App Payment', size=255, required=True, help='Name App Payment module (example, paypal, servired, cash_on_delivery,...)'),
        'confirm': fields.boolean('Confirm', help="Confirm order. Sale Order change state draft to done, and generate picking and/or invoice automatlly"),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of payments."),
        'virtual': fields.boolean('Virtual', help="Virtual payment. Example: Paypal"),
     }

zoook_sale_shop_payment_type()

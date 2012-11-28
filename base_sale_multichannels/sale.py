# -*- encoding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2009  Raphaël Valyi                                     #
# Copyright (C) 2010-2011 Akretion Sébastien BEAU                       #
#                                        <sebastien.beau@akretion.com>  #
# Copyright (C) 2011-2012 Camptocamp Guewen Baconnier                   #
# Copyright (C) 2011 by Openlabs Technologies & Consulting (P) Limited  #
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
import pooler
from sets import Set as set
import netsvc
from tools.translate import _
import time
import decimal_precision as dp
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)


class external_shop_group(osv.osv):
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


class ExternalShippingCreateError(Exception):
     """
      This error has to be raised when we tried to create a stock.picking on
      the external referential and the external referential has failed
      to create it. It must be raised only when we are SURE that the
      external referential will never be able to create it!
     """
     pass


class sale_shop(osv.osv):
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

    def _get_referential_id(self, cr, uid, ids, name, args, context=None):
        res = {}
        for shop in self.browse(cr, uid, ids, context=context):
            if shop.shop_group_id:
                res[shop.id] = shop.shop_group_id.referential_id.id
                #path to fix orm bug indeed even if function field are store, the value is not store in the database
                cr.execute('update sale_shop set referential_id = %s where id=%s', (shop.shop_group_id.referential_id.id, shop.id))
            else:
                #path to fix orm bug indeed even if function field are store, the value is never read for many2one fields
                cr.execute('select referential_id from sale_shop where id=%s', (shop.id,))
                result = cr.fetchone()
                res[shop.id] = result[0]
        return res

    def _set_referential_id(self, cr, uid, id, name, value, arg, context=None):
        shop = self.browse(cr, uid, id, context=context)
        if shop.shop_group_id:
            raise osv.except_osv(_("User Error"), _("You can not change the referential of this shop, please change the referential of the shop group!"))
        else:
            if value == False:
                cr.execute('update sale_shop set referential_id = NULL where id=%s', (id,))
            else:
                cr.execute('update sale_shop set referential_id = %s where id=%s', (value, id))
        return True

    def _get_shop_ids(self, cr, uid, ids, context=None):
        shop_ids=[]
        for group in self.pool.get('external.shop.group').browse(cr, uid, ids, context=context):
            shop_ids += [shop.id for shop in group.shop_ids]
        return shop_ids

    def _get_stock_field_id(self, cr, uid, context=None):
        # TODO : Hidden dependency, put in a glue module ?
        if self.pool.get('ir.module.module').is_installed(
            cr, uid, 'stock_available_immediately', context=None):
            stock_field = 'immediately_usable_qty'
        else:
            stock_field = 'virtual_available'

        field_ids = self.pool.get('ir.model.fields').search(
            cr, uid,
            [('model', '=', 'product.product'),
             ('name', '=', stock_field)],
            context=context)
        return field_ids[0]

    _columns = {
        #'exportable_category_ids': fields.function(_get_exportable_category_ids, method=True, type='one2many', relation="product.category", string='Exportable Categories'),
        'exportable_root_category_ids': fields.many2many('product.category', 'shop_category_rel', 'categ_id', 'shop_id', 'Exportable Root Categories'),
        'exportable_product_ids': fields.function(_get_exportable_product_ids, method=True, type='one2many', relation="product.product", string='Exportable Products'),
        'shop_group_id': fields.many2one('external.shop.group', 'Shop Group', ondelete='cascade'),
        'last_inventory_export_date': fields.datetime('Last Inventory Export Time'),
        'last_images_export_date': fields.datetime('Last Images Export Time'),
        'last_update_order_export_date' : fields.datetime('Last Order Update  Time'),
        'last_products_export_date' : fields.datetime('Last Product Export  Time'),
        'referential_id': fields.function(_get_referential_id, fnct_inv = _set_referential_id, type='many2one',
                relation='external.referential', string='External Referential', method=True,
                store={
                    'sale.shop': (lambda self, cr, uid, ids, c=None: ids, ['shop_group_id'], 10),
                    'external.shop.group': (_get_shop_ids, ['referential_id'], 10),
                 }),
        'is_tax_included': fields.boolean('Prices Include Tax', help="Does the external system work with Taxes Inclusive Prices ?"),
        'sale_journal': fields.many2one('account.journal', 'Sale Journal'),
        'order_prefix': fields.char('Order Prefix', size=64),
        'default_payment_method': fields.char('Default Payment Method', size=64),
        'default_language': fields.many2one('res.lang', 'Default Language'),
        'default_fiscal_position': fields.many2one('account.fiscal.position', 'Default Fiscal Position'),
        'default_customer_account': fields.many2one('account.account', 'Default Customer Account'),
        'auto_import': fields.boolean('Automatic Import'),
        'address_id':fields.many2one('res.partner.address', 'Address'),
        'website': fields.char('Website', size=64),
        'image':fields.binary('Image', filters='*.png,*.jpg,*.gif'),
        'use_external_tax': fields.boolean(
            'Use External Taxes',
            help="If activated, the external taxes will be applied.\n"
                 "If not activated, OpenERP will compute them "
                 "according to default values and fiscal positions."),
        'import_orders_from_date': fields.datetime('Only created after'),
        'check_total_amount': fields.boolean('Check Total Amount', help="The total amount computed by OpenERP should match with the external amount, if not the sale order can not be confirmed."),
        'product_stock_field_id': fields.many2one(
            'ir.model.fields',
            string='Stock Field',
            domain="[('model', 'in', ['product.product', 'product.template']),"
                   " ('ttype', '=', 'float')]",
            help="Choose the field of the product which will be used for "
                 "stock inventory updates.\nIf empty, Quantity Available "
                 "is used")
    }

    _defaults = {
        'payment_default_id': lambda * a: 1, #required field that would cause trouble if not set when importing
        'auto_import': lambda * a: True,
        'product_stock_field_id': _get_stock_field_id,
    }

    def _get_pricelist(self, cr, uid, shop):
        if shop.pricelist_id:
            return shop.pricelist_id.id
        else:
            return self.pool.get('product.pricelist').search(cr, uid, [('type', '=', 'sale'), ('active', '=', True)])[0]

    def export_categories(self, cr, uid, shop, context=None):
        if context is None:
            context = {}
        categories = set([])
        categ_ids = []
        for category in shop.exportable_root_category_ids:
            categ_ids = self.pool.get('product.category')._get_recursive_children_ids(cr, uid, [category.id], "", [], context)[category.id]
            for categ_id in categ_ids:
                categories.add(categ_id)
        context['shop_id'] = shop.id
        self.pool.get('product.category').ext_export(cr, uid, [categ_id for categ_id in categories], [shop.referential_id.id], {}, context)

    def export_products_collection(self, cr, uid, shop, context):
        product_to_export = context.get('force_product_ids', [product.id for product in shop.exportable_product_ids])
        self.pool.get('product.product').ext_export(cr, uid, product_to_export, [shop.referential_id.id], {}, context)

    def export_products(self, cr, uid, shop, context):
        self.export_products_collection(cr, uid, shop, context)

    def export_catalog(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context = dict(context, use_external_log=True)
        for shop in self.browse(cr, uid, ids):
            context['shop_id'] = shop.id
            context['conn_obj'] = shop.referential_id.external_connection()
            self.export_categories(cr, uid, shop, context)
            cr.commit()
            self.export_products(cr, uid, shop, context)
            cr.commit()
        self.export_inventory(cr, uid, ids, context)
        return False

    def export_inventory(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        stock_move_obj = self.pool.get('stock.move')
        for shop in self.browse(cr, uid, ids):
            connection = shop.referential_id.external_connection()

            product_ids = [product.id for product
                           in shop.exportable_product_ids]
            if shop.last_inventory_export_date:
                # we do not exclude canceled moves because it means
                # some stock levels could have increased since last export
                recent_move_ids = stock_move_obj.search(
                    cr, uid,
                    [('write_date', '>', shop.last_inventory_export_date),
                     ('product_id', 'in', product_ids),
                     ('state', '!=', 'draft')],
                    context=context)
            else:
                recent_move_ids = stock_move_obj.search(
                    cr, uid,
                    [('product_id', 'in', product_ids)],
                    context=context)

            recent_moves = stock_move_obj.browse(
                cr, uid, recent_move_ids, context=context)

            product_ids = [move.product_id.id
                           for move
                           in recent_moves
                           if move.product_id.state != 'obsolete']
            product_ids = list(set(product_ids))

            for p_id in product_ids:
                self.pool.get('product.product').export_inventory(
                    cr, uid, [p_id], shop.id, connection, context=context)
            shop.write({'last_inventory_export_date':
                            time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return True

    def import_catalog(self, cr, uid, ids, context):
        #TODO import categories, then products
        raise osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))

    def import_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for shop in self.browse(cr, uid, ids):
            if not shop.company_id.id:
                raise osv.except_osv(_('Warning!'), _('You have to set a company for this OpenERP sale shop!'))

            defaults = {
                            'pricelist_id':self._get_pricelist(cr, uid, shop),
                            'shop_id': shop.id,
                            'fiscal_position': shop.default_fiscal_position.id,
                            'ext_payment_method': shop.default_payment_method,
                            'company_id': shop.company_id.id,
                        }

            context.update({
                            'conn_obj': shop.referential_id.external_connection(),
                            'shop_name': shop.name,
                            'shop_id': shop.id,
                            'external_referential_type': shop.referential_id.type_id.name,
                            'order_prefix': shop.order_prefix,
                            'use_external_tax': shop.use_external_tax,
                        })

            if shop.is_tax_included:
                context.update({'price_is_tax_included': True})

            self.import_shop_orders(cr, uid, shop, defaults, context)
        return False

    def import_shop_orders(self, cr, uid, shop, defaults, context):
        """Not Implemented in abstract base module!"""
        return {}

    def _update_order_query(self, cr, uid, shop, context=None):
        req = """
            SELECT ir_model_data.res_id, ir_model_data.name
                FROM sale_order
                INNER JOIN ir_model_data ON sale_order.id = ir_model_data.res_id
                WHERE ir_model_data.model='sale.order' AND sale_order.shop_id=%s
                    AND ir_model_data.external_referential_id NOTNULL
        """
        params = (shop.id,)
        if shop.last_update_order_export_date:
            req += "AND sale_order.update_state_date > %s"
            params = (shop.id, shop.last_update_order_export_date)
        return req, params

    def update_orders(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for shop in self.browse(cr, uid, ids):
            context['conn_obj'] = shop.referential_id.external_connection()
            #get all orders, which the state is not draft and the date of modification is superior to the last update, to exports
            cr.execute(*self._update_order_query(cr, uid, shop, context=context))
            results = cr.fetchall()

            for result in results:
                ids = self.pool.get('sale.order').search(cr, uid, [('id', '=', result[0])])
                if ids:
                    id = ids[0]
                    order = self.pool.get('sale.order').browse(cr, uid, id, context)
                    order_ext_id = result[1].split('sale_order/')[1]
                    self.update_shop_orders(cr, uid, order, order_ext_id, context)
                    _logger.info("Successfully updated order with OpenERP id %s and ext id %s in external sale system", id, order_ext_id)
            self.pool.get('sale.shop').write(cr, uid, shop.id, {'last_update_order_export_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return False

    def update_shop_partners(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context.update({'force': True}) #FIXME
        for shop in self.browse(cr, uid, ids):
            context['conn_obj'] = shop.referential_id.external_connection()
            ids = self.pool.get('res.partner').search(cr, uid, [('store_id', '=', self.pool.get('sale.shop').oeid_to_extid(cr, uid, shop.id, shop.referential_id.id, context))])
            self.pool.get('res.partner').ext_export(cr, uid, ids, [shop.referential_id.id], {}, context)
        return True

    def update_shop_orders(self, cr, uid, order, ext_id, context):
        raise osv.except_osv(_("Not Implemented"), _("Not Implemented in abstract base module!"))

    def _export_shipping_query(self, cr, uid, shop, context=None):
        query = """
        SELECT stock_picking.id AS picking_id,
               sale_order.id AS order_id,
               count(pickings.id) AS picking_number
        FROM stock_picking
        LEFT JOIN sale_order
                  ON sale_order.id = stock_picking.sale_id
        LEFT JOIN stock_picking as pickings
                  ON (sale_order.id = pickings.sale_id AND pickings.type='out')
        LEFT JOIN ir_model_data
                  ON stock_picking.id = ir_model_data.res_id
                  AND ir_model_data.model = 'stock.picking'
        LEFT JOIN delivery_carrier
                  ON delivery_carrier.id = stock_picking.carrier_id
        WHERE shop_id = %(shop_id)s
              AND ir_model_data.res_id ISNULL
              AND stock_picking.state = 'done'
              AND stock_picking.state = 'out'
              AND NOT stock_picking.do_not_export
              AND (NOT delivery_carrier.export_needs_tracking
                   OR stock_picking.carrier_tracking_ref IS NOT NULL)
        GROUP BY stock_picking.id,
                 sale_order.id,
                 delivery_carrier.export_needs_tracking,
                 stock_picking.carrier_tracking_ref,
                 stock_picking.backorder_id
        ORDER BY sale_order.id ASC,
                 COALESCE(stock_picking.backorder_id, NULL, 0) ASC"""
        params = {'shop_id': shop.id}
        return query, params

    def export_shipping(self, cr, uid, ids, context):
        picking_obj = self.pool.get('stock.picking')
        for shop in self.browse(cr, uid, ids):
            cr.execute(*self._export_shipping_query(
                            cr, uid, shop, context=context))
            results = cr.dictfetchall()
            if not results:
                _logger.info("There is no shipping to export for the shop '%s' to the external referential", shop.name)
                return True
            context['conn_obj'] = shop.referential_id.external_connection()

            picking_cr = pooler.get_db(cr.dbname).cursor()
            try:
                for result in results:
                    picking_id = result['picking_id']

                    if result["picking_number"] == 1:
                        picking_type = 'complete'
                    else:
                        picking_type = 'partial'

                    ext_shipping_id = False
                    try:
                        ext_shipping_id = picking_obj.create_ext_shipping(
                            picking_cr, uid, picking_id, picking_type,
                            shop.referential_id.id, context)
                    except ExternalShippingCreateError, e:
                        # when the creation has failed on the external
                        # referential and we know that we can never
                        # create it, we flag it as do_not_export
                        # ExternalShippingCreateError raising has to be
                        # correctly handled by create_ext_shipping()
                        picking_obj.write(
                            picking_cr, uid,
                            picking_id,
                            {'do_not_export': True},
                            context=context)

                    if ext_shipping_id:
                        picking_obj.create_external_id_vals(
                            picking_cr,
                            uid,
                            picking_id,
                            ext_shipping_id,
                            shop.referential_id.id,
                            context=context)
                        _logger.info("Successfully creating shipping with OpenERP id %s and ext id %s in external sale system", result["picking_id"], ext_shipping_id)
                    picking_cr.commit()
            finally:
                picking_cr.close()
        return True

sale_shop()


class sale_order(osv.osv):
    _inherit = "sale.order"

    def _get_payment_type_id(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        pay_type_obj = self.pool.get('base.sale.payment.type')
        for sale in self.browse(cr, uid, ids, context=context):
            res[sale.id] = False
            if not sale.ext_payment_method:
                continue
            pay_type = pay_type_obj.find_by_payment_code(
                cr, uid, sale.ext_payment_method, context=context)
            if not pay_type:
                continue
            res[sale.id] = pay_type.id
        return res

    _columns = {
        'ext_payment_method': fields.char(
            'External Payment Method',
            size=32,
            help="Spree, Magento, Oscommerce... Payment Method"),
        'need_to_update': fields.boolean('Need To Update'),
        'ext_total_amount': fields.float(
            'Origin External Amount',
            digits_compute=dp.get_precision('Sale Price'),
            readonly=True),
        'base_payment_type_id': fields.function(
            _get_payment_type_id,
            string='Payment Type',
            type='many2one',
            relation='base.sale.payment.type',
            store={
                'sale.order':
                    (lambda self, cr, uid, ids, c=None: ids, ['ext_payment_method'], 20),
            }),
        'referential_id': fields.related(
                    'shop_id', 'referential_id',
                    type='many2one', relation='external.referential',
                    string='External Referential'),
        'update_state_date': fields.datetime('Update State Date'),
    }

    _defaults = {
        'need_to_update': lambda *a: False,
    }

    def write(self, cr, uid, ids, vals, context=None):
        if 'state' in vals:
            vals['update_state_date'] = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    def _get_kwargs_onchange_partner_id(self, cr, uid, vals, context=None):
        return {
            'ids': None,
            'part': vals.get('partner_id'),
        }


    #I will probably extract this code in order to put it in a "glue" module
    def _get_kwargs_onchange_partner_invoice_id(self, cr, uid, vals, context=None):
        return {
            'ids': None,
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_id': vals.get('partner_id'),
            'shop_id': vals.get('shop_id'),
        }

    def play_order_onchange(self, cr, uid, vals, defaults=None, context=None):
        ir_module_obj= self.pool.get('ir.module.module')
        vals = self.call_onchange(cr, uid, 'onchange_partner_id', vals, defaults, context=context)
        if ir_module_obj.is_installed(cr, uid, 'account_fiscal_position_rule_sale', context=context):
            vals = self.call_onchange(cr, uid, 'onchange_partner_invoice_id', vals, defaults, context=context)
        return vals

    def merge_with_default_value(self, cr, uid, sub_mapping_list, external_data, external_referential_id, vals, defaults=None, context=None):
        pay_type_obj = self.pool.get('base.sale.payment.type')
        payment_method = vals.get('ext_payment_method', False)
        payment_settings = pay_type_obj.find_by_payment_code(
            cr, uid, payment_method, context=context)
        if payment_settings:
            vals['order_policy'] = payment_settings.order_policy
            vals['picking_policy'] = payment_settings.picking_policy
            vals['invoice_quantity'] = payment_settings.invoice_quantity

        # some vals are in default but are to be prior on the on change
        # vals (on change vals are prior to default vals)
        prior_keys = ['partner_order_id',
                      'partner_invoice_id',
                      'partner_shipping_id']
        vals.update(dict([(key, value) for key, value
                                       in defaults.iteritems()
                                       if key in prior_keys]))
        # update vals with order onchange in order to compute taxes
        vals = self.play_order_onchange(
            cr, uid, vals, defaults=defaults, context=context)
        return super(sale_order, self).merge_with_default_value(cr, uid, sub_mapping_list, external_data, external_referential_id, vals, defaults=defaults, context=context)

    def create_payments(self, cr, uid, order_id, data_record, context):
        """not implemented in this abstract module"""
        if not context.get('external_referential_type'):
            raise osv.except_osv(
                _('Error'), _('Missing external referential type '
                              ' when creating payment'))
        return False

    def _parse_external_payment(self, cr, uid, data, context=None):
        """
        Not implemented in this abstract module

        Parse the external order data and return if the sale order
        has been paid and the amount to pay or to be paid

        :param dict data: payment information of the magento sale
            order
        :return: tuple where :
            - first item indicates if the payment has been done (True or False)
            - second item represents the amount paid or to be paid
        """
        return False, 0.0

    def oe_status_and_paid(self, cr, uid, order_id, external_data, external_referential_id, context):
        """
        Call the methods to check the status and payment
        of an order when we create it from an external

        :param order_id: id of the order
        :param external_data: data of the order on Magento
        :param external_referential_id: id of the external referential
        :return:
        """
        is_paid, amount = self._parse_external_payment(
            cr, uid, external_data, context=context)

        # create_payments has to be called after oe_status
        # because oe_status may create an invoice
        self.oe_status(cr, uid, order_id, is_paid, context)
        self.create_payments(cr, uid, order_id, external_data, context)
        return order_id

    def after_oe_create(self, cr, uid, rec_id, external_data, external_referential_id, context=None):
        """
        Call method to check the status and payment and trigger the next
        validation defined on the payment type.

        :param rec_id: id of the resource created in OpenERP
        :param external_data: dict of vals received from the external referential
        :param external_referential_id: id of the external referential
        :return: True
        """
        self.oe_status_and_paid(cr, uid, rec_id, external_data,
                                external_referential_id, context=context)
        return super(sale_order, self).after_oe_create(
            cr, uid, rec_id, external_data, external_referential_id, context=context)

    def generate_payment_from_order(self, cr, uid, ids, payment_ref, entry_name=None, paid=True, date=None, context=None):
        if type(ids) in [int, long]:
            ids = [ids]
        res = []
        for order in self.browse(cr, uid, ids, context=context):
            id = self.generate_payment_with_pay_code(cr, uid,
                                                    order.ext_payment_method,
                                                    order.partner_id.id,
                                                    order.ext_total_amount or order.amount_total,
                                                    payment_ref,
                                                    entry_name or order.name,
                                                    date or order.date_order,
                                                    paid,
                                                    context)
            id and res.append(id)
        return res

    def generate_payment_with_pay_code(self, cr, uid, payment_code, partner_id,
                                       amount, payment_ref, entry_name,
                                       date, paid, context):
        # avoid to create a payment without amount:
        # the invoice will never be reconciled with the payment
        if not amount:
            return False
        pay_type_obj = self.pool.get('base.sale.payment.type')
        payment_settings = pay_type_obj.find_by_payment_code(
            cr, uid, payment_code, context=context)
        if payment_settings and \
           payment_settings.journal_id and \
           (payment_settings.check_if_paid and
            paid or not payment_settings.check_if_paid):
            return self.generate_payment_with_journal(
                cr, uid, payment_settings.journal_id.id,
                partner_id, amount, payment_ref,
                entry_name, date, payment_settings.validate_payment,
                context=context)
        return False

    def generate_payment_with_journal(self, cr, uid, journal_id, partner_id,
                                      amount, payment_ref, entry_name,
                                      date, should_validate, context):
        """
        Generate a voucher for the payment

        It will try to match with the invoice of the order by
        matching the payment ref and the invoice origin.

        The invoice does not necessarily exists at this point, so if yes,
        it will be matched in the voucher, otherwise, the voucher won't
        have any invoice lines and the payment lines will be reconciled
        later with "auto-reconcile" if the option is used.

        """
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        move_line_obj = self.pool.get('account.move.line')

        journal = self.pool.get('account.journal').browse(
            cr, uid, journal_id, context=context)

        voucher_vals = {'reference': entry_name,
                        'journal_id': journal.id,
                        'amount': amount,
                        'date': date,
                        'partner_id': partner_id,
                        'account_id': journal.default_credit_account_id.id,
                        'currency_id': journal.company_id.currency_id.id,
                        'company_id': journal.company_id.id,
                        'type': 'receipt', }
        voucher_id = voucher_obj.create(cr, uid, voucher_vals, context=context)

        # call on change to search the invoice lines
        onchange_voucher = voucher_obj.onchange_partner_id(
            cr, uid, [],
            partner_id=partner_id,
            journal_id=journal.id,
            amount=amount,
            currency_id=journal.company_id.currency_id.id,
            ttype='receipt',
            date=date,
            context=context)['value']

        # keep in the voucher only the move line of the
        # invoice (eventually) created for this order
        matching_line = {}
        if onchange_voucher.get('line_cr_ids'):
            voucher_lines = onchange_voucher['line_cr_ids']
            line_ids = [line['move_line_id'] for line in voucher_lines]
            matching_ids = [line.id for line
                            in move_line_obj.browse(
                                cr, uid, line_ids, context=context)
                            if line.ref == entry_name]
            matching_lines = [line for line
                              in voucher_lines
                              if line['move_line_id'] in matching_ids]
            if matching_lines:
                matching_line = matching_lines[0]
                matching_line.update({
                    'amount': amount,
                    'voucher_id': voucher_id,
                })

        if matching_line:
            voucher_line_obj.create(cr, uid, matching_line, context=context)
        if should_validate:
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(
                uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
        return voucher_id

    def _apply_payment_settings(self, cr, uid, order, paid, context=None):
        payment_settings = order.base_payment_type_id
        if payment_settings:
            if payment_settings.payment_term_id:
                self.write(cr, uid, order.id, {'payment_term': payment_settings.payment_term_id.id})

            if payment_settings.check_if_paid and not paid:
                if order.state == 'draft' and datetime.strptime(order.date_order, DEFAULT_SERVER_DATE_FORMAT) < datetime.now() - relativedelta(days=payment_settings.days_before_order_cancel or 30):
                    self.init_auto_wkf_cancel( cr, uid, order, context=context)
                    self.write(cr, uid, order.id, {'need_to_update': False})
                    #TODO eventually call a trigger to cancel the order in the external system too
                    _logger.info("order %d canceled in OpenERP because older than %d days and still not confirmed",
                                order.id, payment_settings.days_before_order_cancel or 30)
                else:
                    self.write(cr, uid, order.id, {'need_to_update': True})
            else:
                if payment_settings.validate_order:
                    self.init_auto_wkf_validate(cr, uid, order, context=context)
                    self.write(cr, uid, order.id, {'need_to_update': False})
        return True

    def oe_status(self, cr, uid, ids, paid=True, context=None):
        if type(ids) in [int, long]:
            ids = [ids]

        auto_wkf_obj = self.pool.get('auto.workflow.job')
        for order in self.browse(cr, uid, ids, context):
            self._apply_payment_settings(cr, uid, order, paid, context=context)
        return True

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) lines: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        if order.shop_id.sale_journal:
            vals['journal_id'] = order.shop_id.sale_journal.id
        return vals

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv = False, context=None):
        inv_obj = self.pool.get('account.invoice')
        job_obj = self.pool.get('base.sale.auto.reconcile.job')
        res = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states, date_inv, context)
        for order in self.browse(cr, uid, ids, context=context):
            payment_settings = order.base_payment_type_id
            if payment_settings and payment_settings.invoice_date_is_order_date:
                inv_obj.write(cr, uid, [inv.id for inv in order.invoice_ids], {'date_invoice' : order.date_order}, context=context)
            if order.order_policy == 'postpaid':
                for invoice in order.invoice_ids:
                    self.init_auto_wkf_invoice(cr, uid, order, invoice.id, context=context)
        return res

    def oe_update(self, cr, uid, existing_rec_id, vals, each_row, external_referential_id, defaults, context):
        '''Not implemented in this abstract module, if it's not implemented in your module it will raise an error'''
        # Explication :
        # sometime customer can do ugly thing like renamming a sale_order and try to reimported it,
        # sometime openerp run two scheduler at the same time, or the customer launch two openerp at the same time
        # or the external system give us again an already imported order
        # As the update of an existing order (this is not the update of the status but the update of the line, the address...)
        # is not supported by base_sale_multichannels and also not in magentoerpconnect.
        # It's better to don't allow this feature to avoid hidding a problem.
        # It's better to have the order not imported and to know it than having order with duplicated line.
        if not (context and context.get('oe_update_supported', False)):
            #TODO found a clean solution to raise the osv.except_osv error in the try except of the function import_with_try
            raise osv.except_osv(_("Not Implemented"), _(("The order with the id %s try to be updated from the external system"
                                "This feature is not supported. Maybe the import try to reimport an existing sale order"%(existing_rec_id,))))
        return existing_rec_id

sale_order()


class sale_order_line(osv.osv):
    _inherit='sale.order.line'

    _columns = {
        'ext_product_ref': fields.char('Product Ext Ref', help="This is the original external product reference", size=256),
    }

    def _get_kwargs_product_id_change(self, cr, uid, line, parent_data, previous_lines, context=None):
        return {
            'ids': None,
            'pricelist': parent_data.get('pricelist_id'),
            'product': line.get('product_id'),
            'qty': float(line.get('product_uom_qty')),
            'uom': line.get('product_uom'),
            'qty_uos': float(line.get('product_uos_qty', 1)),
            'uos': line.get('product_uos'),
            'name': line.get('name'),
            'partner_id': parent_data.get('partner_id'),
            'lang': False,
            'update_tax': True,
            'date_order': parent_data.get('date_order'),
            'packaging': line.get('product_packaging'),
            'fiscal_position': parent_data.get('fiscal_position'),
            'flag': False,
            'context': context,
        }

    def play_sale_order_line_onchange(self, cr, uid, line, parent_data, previous_lines, defaults, context=None):
        line = self.call_onchange(cr, uid, 'product_id_change', line, defaults=defaults, parent_data=parent_data, previous_lines=previous_lines, context=context)
        #TODO all m2m should be mapped correctly
        if line.get('tax_id'):
            line['tax_id'] = [(6, 0, line['tax_id'])]
        return line

    def oevals_from_extdata(self, cr, uid, external_referential_id, data_record, mapping_lines, key_for_external_id=None, parent_data=None, previous_lines=None, defaults=None, context=None):
        line = super(sale_order_line, self).oevals_from_extdata(cr, uid, external_referential_id, data_record, mapping_lines, key_for_external_id=key_for_external_id,  parent_data=parent_data, previous_lines=previous_lines, defaults=defaults, context=context)
        if context.get('use_external_tax'):
            # Get the taxes of the external system
            if line.get('tax_rate'):
                line_tax_id = self.pool.get('account.tax').get_tax_from_rate(cr, uid, line['tax_rate'], context.get('is_tax_included'), context=context)
                line['tax_id'] = [(6, 0, line_tax_id)]
        else:
            # compute the taxes from OpenERP
            line = self.play_sale_order_line_onchange(cr, uid, line, parent_data, previous_lines, defaults, context=context)
        return line

sale_order_line()

class base_sale_payment_type(osv.osv):
    _name = "base.sale.payment.type"
    _description = "Base Sale Payment Type"

    _columns = {
        'name': fields.char('Payment Codes', help="List of Payment Codes separated by ;", size=256, required=True),
        'journal_id': fields.many2one('account.journal','Payment Journal', help='When a Payment Journal is defined on a Payment Type, a Customer Payment (Voucher) will be automatically created once the payment is done on the external system.'),
        'picking_policy': fields.selection([('direct', 'Partial Delivery'), ('one', 'Complete Delivery')], 'Packing Policy'),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice on Order After Delivery'),
            ('picking', 'Invoice from the Packing'),
        ], 'Shipping Policy'),
        'invoice_quantity': fields.selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on'),
        'is_auto_reconcile': fields.boolean('Auto-reconcile', help="If checked, will try to reconcile the Customer Payment (voucher) and the open invoice by matching the origin."),
        'validate_order': fields.boolean('Validate Order'),
        'validate_payment': fields.boolean('Validate Payment in Journal', help='If checked, the Customer Payment (voucher) generated in the  Payment Journal will be validated and reconciled if the invoice already exists.'),
        'create_invoice': fields.boolean('Create Invoice'),
        'validate_invoice': fields.boolean('Validate Invoice'),
        'validate_picking': fields.boolean('Validate Picking'),
        'validate_manufactoring_order': fields.boolean('Validate Manufactoring Order'),
        'check_if_paid': fields.boolean('Check if Paid'),
        'days_before_order_cancel': fields.integer('Days Delay before Cancel', help='number of days before an unpaid order will be cancelled at next status update from Magento'),
        'invoice_date_is_order_date' : fields.boolean('Force Invoice Date', help="If it's check the invoice date will be the same as the order date"),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term'),
    }

    _defaults = {
        'picking_policy': lambda *a: 'direct',
        'order_policy': lambda *a: 'manual',
        'invoice_quantity': lambda *a: 'order',
        'is_auto_reconcile': lambda *a: False,
        'validate_payment': lambda *a: False,
        'validate_invoice': lambda *a: False,
        'days_before_order_cancel': lambda *a: 30,
    }

    def find_by_payment_code(self, cr, uid, payment_code, context=None):
        payment_setting_ids = self.search(
            cr, uid, [['name', 'like', payment_code]], context=context)
        payment_setting = False
        payment_settings = self.browse(
            cr, uid, payment_setting_ids, context=context)
        for pay_type in payment_settings:
            # payment codes are in this form "bankpayment;checkmo"
            payment_codes = [x.strip() for x in pay_type.name.split(';')]
            if payment_code in payment_codes:
                payment_setting = pay_type
                break
        return payment_setting

base_sale_payment_type()


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def validate_picking(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context=context):
            self.force_assign(cr, uid, [picking.id])
            partial_data = {}
            for move in picking.move_lines:
                partial_data["move%s" % (move.id)] = {
                    'product_id': move.product_id.id,
                    'product_qty': move.product_qty,
                    'product_uom': move.product_uom.id,
                    'prodlot_id': move.prodlot_id.id,
                }
            self.do_partial(cr, uid, [picking.id], partial_data, context=context)
        return True

    def validate_manufactoring_order(self, cr, uid, origin, context=None): #we do not create class mrp.production to avoid dependence with the module mrp
        if context is None:
            context = {}
        wf_service = netsvc.LocalService("workflow")
        mrp_prod_obj = self.pool.get('mrp.production')
        mrp_product_produce_obj = self.pool.get('mrp.product.produce')
        production_ids = mrp_prod_obj.search(cr, uid, [('origin', 'ilike', origin)])
        for production in mrp_prod_obj.browse(cr, uid, production_ids):
            mrp_prod_obj.force_production(cr, uid, [production.id])
            wf_service.trg_validate(uid, 'mrp.production', production.id, 'button_produce', cr)
            context.update({'active_model': 'mrp.production', 'active_ids': [production.id], 'search_default_ready': 1, 'active_id': production.id})
            produce = mrp_product_produce_obj.create(cr, uid, {'mode': 'consume_produce', 'product_qty': production.product_qty}, context)
            mrp_product_produce_obj.do_produce(cr, uid, [produce], context)
            self.validate_manufactoring_order(cr, uid, production.name, context)
        return True

stock_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

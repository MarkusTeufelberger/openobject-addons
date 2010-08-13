# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 Gábor Dukai <gdukai@gmail.com>
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
from tools import config
from tools.translate import _

class product_pricelist_wizard_line(osv.osv_memory):
    _name = 'product.pricelist.wizard.line'

    _columns = {
        'price_version_id': fields.many2one('product.pricelist.version', 'Price List Version', required=True, readonly=True),
        'item_ids': fields.one2many('product.pricelist.wizard.item', 'wizard_line_id', 'Price List Items', context={'allow_delete': True}),
        'categ_id': fields.many2one('product.category','Category', readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        plitem_obj = self.pool.get('product.pricelist.item')
        witem_obj = self.pool.get('product.pricelist.wizard.item')
        line_id = super(product_pricelist_wizard_line, self).create(cr, uid, vals, context)
        plitem_ids = plitem_obj.search(cr, uid, \
            [('price_version_id','=',vals['price_version_id']), '|', \
            ('product_id','in',context['prod_ids']), '|', ('product_tmpl_id','in',context['tmpl_ids']), \
            ('categ_id','in',context['categ_ids'])])
        plitem_ids.extend(plitem_obj.search(cr, uid, \
            [('price_version_id','=',vals['price_version_id']), \
            ('product_id','=',False), ('product_tmpl_id','=',False), \
            ('categ_id','=',False)]))
        for plitem in plitem_obj.browse(cr, uid, plitem_ids):
            d = {}
            d['wizard_line_id'] = line_id
            d['item_id'] = plitem.id
            for f in ('categ_id', 'product_tmpl_id', 'product_id',
                      'base_pricelist_id', ):
                d[f] = eval('plitem.' + f + '.id')
            for f in ('name', 'min_quantity', 'sequence', 'base',
                      'price_surcharge', 'price_discount', 'price_round',
                      'price_min_margin', 'price_max_margin', ):
                d[f] = getattr(plitem, f)
            witem_obj.create(cr, uid, d)
        return line_id

product_pricelist_wizard_line()

class product_pricelist_wizard_item(osv.osv_memory):
    def _price_field_get(self, cr, uid, context={}):
        plitem_obj = self.pool.get('product.pricelist.item')
        return plitem_obj._price_field_get(cr, uid, context)

    _name = "product.pricelist.wizard.item"
    _description = "Pricelist item"
    _order = "sequence, min_quantity desc"
    _defaults = {
        'base': lambda *a: -1,
        'min_quantity': lambda *a: 0,
        'sequence': lambda *a: 5,
        'price_discount': lambda *a: 0,
    }
    _columns = {
        'item_id': fields.many2one('product.pricelist.item', 'Price List Item', required=True),
        'name': fields.char('Rule Name', size=64, help="Explicit rule name for this pricelist line."),
        'wizard_line_id': fields.many2one('product.pricelist.wizard.line', 'Wizard Line', required=True),
        'product_tmpl_id': fields.many2one('product.template', 'Product Template', ondelete='cascade', help="Set a template if this rule only apply to a template of product. Keep empty for all products"),
        'product_id': fields.many2one('product.product', 'Product', ondelete='cascade', help="Set a product if this rule only apply to one product. Keep empty for all products"),
        'categ_id': fields.many2one('product.category', 'Product Category', ondelete='cascade', help="Set a category of product if this rule only apply to products of a category and his childs. Keep empty for all products"),

        'min_quantity': fields.integer('Min. Quantity', required=True, help="The rule only applies if the partner buys/sells more than this quantity."),
        'sequence': fields.integer('Sequence', required=True),
        'base': fields.selection(_price_field_get, 'Based on', required=True, size=-1, help="The mode for computing the price for this rule."),
        'base_pricelist_id': fields.many2one('product.pricelist', 'If Other Pricelist'),

        'price_surcharge': fields.float('Price Surcharge',
            digits=(16, int(config['price_accuracy']))),
        'price_discount': fields.float('Price Discount', digits=(16,4)),
        'price_round': fields.float('Price Rounding',
            digits=(16, int(config['price_accuracy'])),
            help="Sets the price so that it is a multiple of this value.\n" \
              "Rounding is applied after the discount and before the surcharge.\n" \
              "To have prices that end in 9.99, set rounding 10, surcharge -0.01" \
            ),
        'price_min_margin': fields.float('Min. Price Margin',
            digits=(16, int(config['price_accuracy']))),
        'price_max_margin': fields.float('Max. Price Margin',
            digits=(16, int(config['price_accuracy']))),
    }
    def product_id_change(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {}
        prod = self.pool.get('product.product').browse(cr, uid, product_id)
        res = {'sequence': 10}
        if prod.partner_ref:
            res['name'] = prod.partner_ref
        return {'value': res}

    def product_tmpl_id_change(self, cr, uid, ids, prod_tmpl_id, context=None):
        if not prod_tmpl_id:
            return {}
        prod = self.pool.get('product.template').browse(cr, uid, prod_tmpl_id)
        res = {'sequence': 15,
               'name': prod.name,}
        return {'value': res}

    def categ_id_change(self, cr, uid, ids, categ_id, context=None):
        if not categ_id:
            return {}
        categ = self.pool.get('product.category').browse(cr, uid, categ_id, context)
        res = {'name': categ.complete_name}
        decision = {
            '0': 20,
            '1': 30,
            '2': 40,
        }
        if categ.sl_level:
            res['sequence'] = decision[categ.sl_level]
        return {'value': res}

    def write(self, cr, uid, ids, vals, context=None):
        vals2 = vals.copy()
        plitem_id = vals2.pop('item_id', False)
        if not plitem_id:
            plitem_id = self.browse(cr, uid, ids[0]).item_id.id
        vals2.pop('wizard_line_id', False)
        if 'wizard_line_id' in vals:
            vals2['price_version_id'] = self.pool.get('product.pricelist.wizard.line')\
                .browse(cr, uid, vals['wizard_line_id']).price_version_id.id
        self.pool.get('product.pricelist.item').write(cr, uid, plitem_id, vals2, None)
        return super(product_pricelist_wizard_item, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context=None):
        if 'item_id' not in vals:
            vals2 = vals.copy()
            vals2.pop('item_id', False)
            vals2.pop('wizard_line_id', False)
            vals2['price_version_id'] = self.pool.get('product.pricelist.wizard.line')\
                .browse(cr, uid, vals['wizard_line_id']).price_version_id.id
            plitem_id = self.pool.get('product.pricelist.item').create(cr, uid, vals2, None)
            vals['item_id'] = plitem_id
        return super(product_pricelist_wizard_item, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context={}):
        """Deletes the original pricelist items that are mirrored by the wizard.item.
        Because the osv_memory vaccum() method likes to trigger this unlink() method
        to remove unused osv_memories, we need to make sure unlink() was called from the
        user interface. That's what 'allow_delete' is for."""
        if context.get('allow_delete', False):
            items = self.read(cr, uid, ids, ['item_id'])
            unlink_ids = []
            for t in items:
                unlink_ids.append(t['item_id'])
            self.pool.get('product.pricelist.item').unlink(cr, uid, unlink_ids, None)
        return super(product_pricelist_wizard_item, self).unlink(cr, uid, ids, context=context)

product_pricelist_wizard_item()



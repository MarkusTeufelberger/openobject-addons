##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: sale.py 1005 2005-07-25 08:41:42Z nicoe $
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

import pooler
import wizard

_export_done_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Product Export">
    <separator string="Products exported" colspan="4" />
    <field name="prod_new"/>
    <newline/>
    <field name="prod_update"/>
    <newline/>
    <field name="prod_delete"/>
</form>'''

_export_done_fields = {
    'prod_new': {'string':'New products', 'type':'float', 'readonly': True},
    'prod_update': {'string':'Updated products', 'type':'float', 'readonly': True},
    'prod_delete': {'string':'Deleted products', 'type':'float', 'readonly': True},
}

def _do_export(self, cr, uid, data, context):
    self.pool = pooler.get_pool(cr.dbname)
    esale_category_obj = self.pool.get('esale.oscom.category')
    product_obj = self.pool.get('product.product')

    product_ids = data['ids']
    category_ids_dict = {}
    products = product_obj.browse(cr, uid, product_ids)
    if len(product_ids) > 1:
        for product in products:
            product_by_category_list = category_ids_dict.get(product.categ_id.id, False)
            if product_by_category_list and len(product_by_category_list):
                product_by_category_list.append(product.id)
            else:
                category_ids_dict[product.categ_id.id] = [product.id]
        for category_id in category_ids_dict:
            web_categ_id = esale_category_obj.search(cr, uid, [('category_id','=',category_id)])
            if not len (web_categ_id):
                raise wizard.except_wizard(_('User Error'), _('Select only products which belong to a web category!'))
    else:
        oerp_category_id = products[0].categ_id.id
        web_categ_id = esale_category_obj.search(cr, uid, [('category_id','=',oerp_category_id)])
        if not len(web_categ_id):
            raise wizard.except_wizard(_('User Error'), _('This product must belong to a web category!'))

    return product_obj.oscom_export(cr, uid, product_ids=product_ids, context=context)


class wiz_esale_oscom_select_products(wizard.interface):
    states = { 'init' : { 'actions' : [_do_export],
                          'result' : { 'type' : 'form',
                                       'arch' : _export_done_form,
                                       'fields' : _export_done_fields,
                                       'state' : [('end', 'End')]
                                     }
                        }
             }

wiz_esale_oscom_select_products('esale.oscom.select.products');

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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
"""Adds new fields to product objects"""

from osv import osv,fields
from tools.translate import _

class product_product(osv.osv):
    """adds new fields"""

    _inherit = "product.product"

    _columns = {
        'property_ids': fields.many2many('mrp.property', 'product_product_property_rel', 'product_id','property_id', 'Properties'),
        'variants': fields.char('Variants', type='char', size=256, readonly=True),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        """evita que se dupliquen las variantes cuando se ejecuta esta acción"""
        if default is None:
            default = {}
        default = default.copy()
        default.update({'variant_ids':False,})
        return super(product_product, self).copy(cr, uid, id, default, context)


product_product()

class product_template(osv.osv):
    """Allows associate property groups to product templates for creating variants"""
    _inherit = "product.template"

    _columns = {
        'property_group_ids': fields.one2many('product.property.attributes.rel', 'product_tmpl_id', 'Property Groups'),
        'variant_ids':fields.one2many('product.product', 'product_tmpl_id', 'Variants'),
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        """cuando se duplique no duplicará las variantes de la plantilla de poducto"""
        if default is None:
            default = {}
        default = default.copy()
        default.update({'variant_ids':False,})
        return super(product_template, self).copy(cr, uid, id, default, context)


    def _get_variant_name(self, cr, uid, properties_ids, context=None):
        """
        Devuelve el nombre 'descriptivo' de la variante.
        Muestra el los GRUPOS de la variante con cada uno de sus ATRIBUTOS
        """
        if context is None: context = {}

        property_cmp = {}
        variant_name = ''

        for property in self.pool.get('mrp.property').browse(cr, uid, properties_ids, context=context):
            if property.group_id.name not in property_cmp:
                property_cmp[property.group_id.name] = '%s: %s' % (property.group_id.name, (property.code and  "%s %s" % (property.code, property.name) or property.name))
            else:
                property_cmp[property.group_id.name] += ", %s" % (property.code and  "%s %s" % (property.code, property.name) or property.name)

        variant_name = ", ".join([property_cmp[x] for x in property_cmp])

        return variant_name
    
    def button_generate_variants(self, cr, uid, ids, context=None):
        """botón usado para generar las variantes"""
        if context is None: context = {}

        def cartesian_product(args):
            if len(args) == 1: return [(x,) for x in args[0]]
            return [(i,) + j for j in cartesian_product(args[1:]) for i in args[0]]

        property_group_list=[]
        properties_list=[]

        for product_temp in self.browse(cr, uid, ids, context):
            for property_group in product_temp.property_group_ids:
                property_group_list.append(property_group.property_group_id.id)
                properties_list.append([property.id for property in property_group.property_group_id.property_ids])
                # if last property group has no properties, we ignore it
                if not properties_list[-1]:
                    properties_list.pop()
                    property_group_list.pop()

            code = False
            product_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', product_temp.id)])
            if product_ids:
                product = self.pool.get('product.product').browse(cr, uid, product_ids[0])
                code = product.default_code

            if properties_list:
                list_of_properties = cartesian_product(properties_list)
                cont = 0
                for property_id in list_of_properties:
                    constraints_list = [('property_ids', 'in', [i]) for i in property_id]
                    constraints_list.append(('product_tmpl_id', '=', product_temp.id))
                    cont += 1
                    
                    prod_var = self.pool.get('product.product').search(cr, uid, constraints_list)
                    if not prod_var:
                        vals={}
                        vals['product_tmpl_id'] = product_temp.id
                        vals['property_ids'] = [(6, 0, list(property_id))]                        
                        vals['default_code'] = code
                        vals['variants'] = self._get_variant_name(cr, uid, list(property_id), context=context)
                        self.pool.get('product.product').create(cr, uid, vals)
                    else:
                        pass

        return True

product_template()

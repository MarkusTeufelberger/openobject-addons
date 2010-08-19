# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
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

import netsvc
from osv import fields, osv
from tools.translate import _

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'prodlot_test_template_id': fields.many2one('qc.test.template', 'Production Lot Test Template', help='Quality control test the product has to pass before being sold or use for production.'),
    }
product_product()

class stock_production_lot( osv.osv ):
    _inherit = 'stock.production.lot'

    def _requires_sample_library(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for lot in self.browse(cr, uid, ids, context):
            if lot.product_id.bulk_id:
                result[lot.id] = True
            else:
                result[lot.id] = False
        return result

    def _requires_generic_quality_test(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for lot in self.browse(cr, uid, ids, context):
            template_ids = self.pool.get('qc.test.template').search(cr, uid, [('type','=','generic')], context=context)
            if template_ids:
                result[lot.id] = True
            else:
                result[lot.id] = False
        return result

    def _requires_specific_quality_test(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for lot in self.browse(cr, uid, ids, context):
            template_ids = self.pool.get('qc.test.template').search(cr, uid, [('object_id','=','product.product,%d' % lot.product_id.id)], context=context)
            if template_ids:
                result[lot.id] = True
            else:
                result[lot.id] = False
        return result

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'generic_quality_test_id': fields.many2one('qc.test', 'Generic Quality Test', readonly=True),
        'requires_generic_quality_test': fields.function(_requires_generic_quality_test, method=True, type='boolean', string='Requires Sample Library'),
        'specific_quality_test_id': fields.many2one('qc.test', 'Specific Quality Test', readonly=True),
        'requires_specific_quality_test': fields.function(_requires_specific_quality_test, method=True, type='boolean', string='Requires Sample Library'),
        'state': fields.selection([
            ('draft','Draft'),
            ('generic-qc','Waiting Generic Quality Control'),
            ('failed-g-qc', 'Generic Quality Control Failed'),
            ('sample-library','Waiting Sample Library'),
            ('specific-qc','Waiting Specific Quality Control'),
            ('success-s-qc','Specific Quality Control Succeeded'),
            ('failed-s-qc','Specific Quality Control Failed'),
        ], 'State', required=True, readonly=True, help='A production lot can be in one of the following states: Draft, Waiting Sample Library, Waiting Quality Control, Valid (passed quality tests) or Invalid (did not pass quality tests).'),
        'requires_sample_library': fields.function(_requires_sample_library, method=True, type='boolean', string='Requires Sample Library'),
        'sample_library_code': fields.integer('Sample Library Code', readonly=True),
    }
    _defaults = {
        'state': lambda *a: 'draft',
    }

    def action_generic_quality_control_get(self, cr, uid, ids, context=None):
        id = ids[0]

        prodlot = self.browse(cr, uid, id, context)
        if prodlot.generic_quality_test_id:
            return prodlot.generic_quality_test_id.id

        test_id = False
        template_ids = self.pool.get('qc.test.template').search(cr, uid, [('type','=','generic')], context=context)
        if template_ids:
            reference = 'stock.production.lot,%d' % id
            test_id = self.pool.get('qc.test').create(cr, uid, {
                'object_id': reference,
            }, context)
            self.pool.get('qc.test').set_test_template(cr, uid, [test_id], template_ids[0], context)

        self.write(cr, uid, ids, {
            'generic_quality_test_id': test_id,
        }, context)
        return test_id

    def action_disable_generic_quality_control(self, cr, uid, ids, context=None):
        id = ids[0]
        prodlot = self.browse(cr, uid, id, context)
        # Check if generic_quality_test_id exists because product may not require a generic quality test
        if prodlot.generic_quality_test_id:
            self.pool.get('qc.test').write(cr, uid, [prodlot.generic_quality_test_id.id], {
                'enabled': False,
            }, context)
        return True
        
    def action_specific_quality_control_get(self, cr, uid, ids, context=None):
        id = ids[0]

        prodlot = self.browse(cr, uid, id, context)
        if prodlot.specific_quality_test_id:
            return prodlot.specific_quality_test_id.id

        test_id = False
        reference = 'product.product,%d' % prodlot.product_id.id
        template_ids = self.pool.get('qc.test.template').search(cr, uid, [('object_id','=',reference)], context=context)
        if template_ids:
            reference = 'stock.production.lot,%d' % id
            test_id = self.pool.get('qc.test').create(cr, uid, {
                'object_id': reference,
            }, context)
            self.pool.get('qc.test').set_test_template(cr, uid, [test_id], template_ids[0], context)

        self.write(cr, uid, ids, {
            'specific_quality_test_id': test_id,
        }, context)
        return test_id

    def action_sample_library(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'sample_library_code': self.pool.get('ir.sequence').get(cr, uid, 'stock.sample.library'),
        }, context)
        workflow = netsvc.LocalService("workflow")
        workflow.trg_validate(uid, 'stock.production.lot', ids[0], 'sample_library_done', cr)
        return True

stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

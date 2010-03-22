# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context and ( context.get('location_id') or context.get('product_id') ):
            domain = []
            location_id = context.get('location_id')
            if location_id:
                domain.append( ('location_id','=',location_id) )
            product_id = context.get('product_id')
            if product_id:
                domain.append( ('product_id','=',product_id) )

            filter_ids = []
            ids = self.pool.get('stock.report.prodlots').search(cr, uid, domain, context=context)
            for record in self.pool.get('stock.report.prodlots').browse(cr, uid, ids, context):
                filter_ids.append( record.prodlot_id.id )
            args = args[:]
            args.append( ('id','in',filter_ids) )
        return super(stock_production_lot, self).search(cr, uid, args, offset, limit, order, context, count)
stock_production_lot()


class product_product(osv.osv):
    _inherit = 'product.product'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context and context.get('location'):
            location_id = context['location']
            filter_ids = []
            ids = self.pool.get('stock.report.prodlots').search(cr, uid, [('location_id','=',location_id)], context=context)
            for record in self.pool.get('stock.report.prodlots').browse(cr, uid, ids, context):
                filter_ids.append( record.product_id.id )
            args = args[:]
            args.append( ('id','in',filter_ids) )
        return super(product_product, self).search(cr, uid, args, offset, limit, order, context, count)

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

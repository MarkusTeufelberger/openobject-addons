# -*- encoding: utf-8 -*-

from osv import osv

class product_product(osv.osv):
    _inherit = 'product.product'

    def price_get(self, cr, uid, ids, ptype='list_price', context={}):
        result = super(product_product, self).price_get(cr, uid, ids, ptype, context)
        
        if 'price_tax_included' in context:
            prctype_obj = self.pool.get('product.price.type')
            tax_obj = self.pool.get('account.tax')
            prctype_ids = prctype_obj.search(cr, uid, [('field','=',ptype)])
            prctype = prctype_obj.browse(cr, uid, prctype_ids)[0]
            if context['price_tax_included'] and not prctype.price_tax_included:
                for prod in self.browse(cr, uid, ids, context=context):
                    for tax in tax_obj.compute(cr, uid, prod.taxes_id,
                        getattr(prod, ptype), 1):
                        result[prod.id] += tax['amount']
            if not context['price_tax_included'] and prctype.price_tax_included:
                for prod in self.browse(cr, uid, ids, context=context):
                    for tax in tax_obj.compute_inv(cr, uid, prod.taxes_id,
                        getattr(prod, ptype), 1):
                        result[prod.id] -= tax['amount']
        return result
    
product_product()
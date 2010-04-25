# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2009,2010  All Rights Reserved.
#
#   NaN Projectes de programari lliure S.L.
#   http://www.nan-tic.com 
#   author: Àngel Àlvarez  - angel@nan-tic.com 
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

from osv import fields,osv

from tools.translate import _
import time
import math

def rounding(f, r, mode='rounding'):
    if not r:
        return f
    if mode == 'up':
        return math.ceil(f / r) * r
    elif mode == 'down':
        return math.floor(f / r) * r
    else:
        return round(f / r) * r

class product_pricelist_category( osv.osv ):
    """
    Add category to pricelist, only for categorize
    """
    _name = 'product.pricelist.category'
    _description = 'Product Pricelist Category'
    _columns = {
        'name': fields.char('Category', size=30 ),
    }
product_pricelist_category()

class product_pricelist( osv.osv ):
    """
    Add category to pricelist, only for categorize
    Change calculation method. Now take care inside [Base On] item rules to find rule to apply.
    Added base_item_rule dependencies to accumulate price, it permits:
        - price = (price calculated on base on pricelist ) * (1.0+(item.price_discount or 0.0)) 
        price calculated on rule, it is passed to base_item_rule to apply discounts, recharges..
    """
    _inherit = 'product.pricelist'

    _columns = {
        'category_id': fields.many2one( 'product.pricelist.category', 'Category'),
    }

    def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        '''
        context = {
            'uom': Unit of Measure (int),
            'partner': Partner ID (int),
            'date': Date of the pricelist (%Y-%m-%d),
        }
        '''

        context = context or {}
        product_obj = self.pool.get('product.product')

        if context and ('partner_id' in context):
            partner = context['partner_id']

        context['partner_id'] = partner
        date = time.strftime('%Y-%m-%d')
        if context and ('date' in context):
            date = context['date']

        result = {}
        for id in ids:
            result[id] = self.price_get2( cr,uid, id,prod_id,qty,date,partner,context)
            if context and ('uom' in context):
                product = product_obj.browse(cr, uid, prod_id)
                uom = product.uos_id or product.uom_id
                result[id] = self.pool.get('product.uom')._compute_price(cr,uid, uom.id, result[id], context['uom'])
        return result


    def check_item( self, cr, uid, item_id, prod_id, qty, date,partner=None, context=None):
        """
        Check if item rule matches requirements.
        """

        context = context or {}
        result = {}
        tmpl_id,categ_ids = self._get_product_category( cr, uid, prod_id )
        
        item = self.pool.get( 'product.pricelist.item').browse( cr, uid, item_id )

        if item.product_id.id != prod_id and item.product_id.id:
            return False
        if item.product_tmpl_id.id != tmpl_id and  item.product_tmpl_id.id:
            return False
        if not item.categ_id.id  and item.categ_id.id  in categ_ids:
            return False
        if item.min_quantity != 0  and   item.min_quantity < qty:
            return False

        return True

    def price_get2(self, cr, uid, pricelist_id, prod_id, qty, date,partner=None,context=None, acc_price=False, base_item_rule=False):
        
        pricelist= self.pool.get( 'product.pricelist' ).browse( cr,uid,pricelist_id)        
        plversion = self._get_pl_version( cr, uid,pricelist_id, date )
        tmpl_id,categ_ids = self._get_product_category( cr, uid, prod_id )
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')

        plv = self.pool.get('product.pricelist.version').browse(cr,uid,plversion['id'])

        if base_item_rule:
            start_item=base_item_rule
            remove = False
        else:
            # Perfomance improvements, serach first item to apply, and decides if its unique o have to go ahead on item rules.
            remove,start_item = self._get_first_item( cr, uid, plversion['id'],prod_id,qty, date,partner,tmpl_id,categ_ids,context )

        if remove and (start_item is None):
            #if no items finded, no item rules can be applied.
            return False
        if start_item:
            i = self.pool.get('product.pricelist.item').browse(cr,uid,start_item )
            if remove:
                #Its final item rule. 
                items = [i]
            else:
                # delete items before first item searched.
                # TODO: Maybe can get interval [first,last] items to be applied.
                items = list(plv.items_id)
                items = items[items.index(i):]
        
        current_item=None
        price = acc_price or False
        for item in items:
            #check if its rule to apply
            itemok = self.check_item( cr, uid, item.id, prod_id, qty, date,partner,context)
            current_item = item
            if item.base == -1:
                if not item.base_pricelist_id:
                    price= acc_price or 0.0
                    break;
                else:
                    price_tmp = self.price_get2( cr,uid, item.base_pricelist_id.id, prod_id,qty,date,partner,context, acc_price )
                    ptype_src = self.browse(cr, uid,item.base_pricelist_id.id, ).currency_id.id
                    price = currency_obj.compute(cr, uid, ptype_src,pricelist.currency_id.id,price_tmp, round=False)
                    if price:
                        break
 
            elif item.base == -2 and itemok and not acc_price:
                where = []
                if partner:
                    where = [('name', '=', partner) ]
                sinfo = supplierinfo_obj.search(cr, uid, [('product_id', '=', tmpl_id)] + where)
                price = 0.0
                if sinfo:
                    cr.execute('select * ' \
                               'from pricelist_partnerinfo ' \
                                'where suppinfo_id in (' + \
                                    ','.join(map(str, sinfo)) + ') ' \
                                    'and min_quantity <= %s ' \
                                'order by min_quantity desc limit 1', (qty,))
                    res2 = cr.dictfetchone()
                    if res2:
                        price = res2['price']
                break
            elif itemok and not acc_price:
                price_type = price_type_obj.browse(cr, uid, item.base )
                price = currency_obj.compute(cr, uid,
                    price_type.currency_id.id, pricelist.currency_id.id,
                    product_obj.price_get(cr, uid, [prod_id],
                    price_type.field)[prod_id], round=False, context=context)
                break
            else:
                price = acc_price or False
                if not acc_price:
                    current_item=None
       
        if current_item:
           price_limit = price
           price = price * (1.0+(item.price_discount or 0.0))
           price = rounding(price, item.price_round, item.rounding_mode)
           price += ( item.price_surcharge or 0.0)
           if item.price_min_margin:
               price = max(price, price_limit+item.price_min_margin)
           if item.price_max_margin:
               price = min(price, price_limit+item.price_max_margin)

           if item.base_itemrule_id:
               # Search nex item_rule base on.. 
               price = self.price_get2( cr,uid, pricelist.id, prod_id,qty,date,partner,context, price, item.base_itemrule_id.id )
        else:
            return acc_price or False
        return price 
        
    def _get_first_item( self, cr, uid, version_id, prod_id, qty, date,partner,tmpl_id,categ_ids, context ):
        #Get sequence of first item on priclist version where depends on other pricelist
        cr.execute(''' select 
                            id,sequence 
                       from    
                            product_pricelist_item 
                       where 
                            base_pricelist_id is not null and
                            price_version_id = ''' + str(version_id) +
                            ''' order by sequence 
                            limit 1''' )
        seq = cr.dictfetchone()
        if categ_ids:
            categ_where = '(categ_id IN (' + ','.join(categ_ids) + '))'
        else:
            categ_where = '(categ_id IS NULL)'

        cr.execute(
                'SELECT i.*, pl.currency_id '
                'FROM product_pricelist_item AS i, '
                    'product_pricelist_version AS v, product_pricelist AS pl '
                'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                    'AND (product_id IS NULL OR product_id = %s) '
                    'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                    'AND price_version_id = %s '
                    'AND (min_quantity IS NULL OR min_quantity <= %s) '
                    'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                'ORDER BY sequence LIMIT 1',
                (tmpl_id, prod_id, version_id, qty))
   
        res = cr.dictfetchone()
        # not item rule base on other pricelist, and final item rule fetched. return (delete all ,id )
        if not seq and res:
            return ( True,res['id'] )
        # not item rule base on other pricelist, and  no final item rule fetched. return (delete all, None )
        elif not seq and not res:
            return (True,None)
        
        # item rule base on other pricelist but first applied final item rule . return (delete all, id)
        if ( res['sequence'] < seq['sequence'] ):
            return (True,res['id'] )

        # item rule base on other pricelist  applied before final item rule . return (delete all=False, id)
        else:
            return (False,seq['id'])

    def _get_pl_version( self, cr, uid, pricelist_id, date ):
        #If accumulate ruleitems, calculate all rule_items.
        #Get current pricelist version.
        cr.execute('SELECT * ' \
                'FROM product_pricelist_version ' \
                'WHERE pricelist_id = %s AND active=True ' \
                'AND (date_start IS NULL OR date_start <= %s) ' \
                'AND (date_end IS NULL OR date_end >= %s) ' \
                'ORDER BY id LIMIT 1', (pricelist_id, date, date))
        plversion = cr.dictfetchone()

        if not plversion:
            raise osv.except_osv(_('Warning !'),
                _('No active version for the selected pricelist !\n' \
                'Please create or activate one.'))
        return plversion

    def _get_product_category( self, cr, uid, prod_id ):
        cr.execute('SELECT id, categ_id ' \
                    'FROM product_template ' \
                    'WHERE id = (SELECT product_tmpl_id ' \
                        'FROM product_product ' \
                        'WHERE id = %s)', (prod_id,))
        tmpl_id, categ = cr.fetchone()
        categ_ids = []
        while categ:
            categ_ids.append(str(categ))
            cr.execute('SELECT parent_id ' \
                        'FROM product_category ' \
                        'WHERE id = %s', (categ,))
            categ = cr.fetchone()[0]
            if str(categ) in categ_ids:
                raise osv.except_osv(_('Warning !'),
                            _('Could not resolve product category, ' \
                              'you have defined cyclic categories ' \
                              'of products!'))                    
        return tmpl_id,categ_ids
product_pricelist()



class product_pricelist_item( osv.osv ):
    _inherit = 'product.pricelist.item'

    def _check_base_item_rule(self, cr, uid, ids, context=None):
        """
        Check that item_rule must have sequence greater then rule.
        """

        item = self.browse( cr,uid, ids[0] )
        if not item.base_itemrule_id.id:
            return True
        if item.sequence > item.base_itemrule_id.sequence:
            return False
        else:
            return True
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        Makes base_item_rule searches on items on pricelist_version and greater sequence.
        """

        if context is None:
            context = {}
        if context.get('ruleitem_id'):
            ctx = context.copy()
            del ctx['ruleitem_id']
            item = self.pool.get('product.pricelist.item').browse( cr, uid, context['ruleitem_id'], ctx )            
            if item.price_version_id.items_id:
                result=[]
                for i in item.price_version_id.items_id:
                    if i.sequence > item.sequence:
                        result.append( i.id )
                args = args[:]
                args.append( ('id', 'in', result) )
        return  super(product_pricelist_item,self).search(cr, uid, args, offset, limit, order, context, count)

    _columns = {
       'base_itemrule_id': fields.many2one( 'product.pricelist.item', 'Other Rule Item', help='The selected item will be used to apply an extra discount on the price resulting from the Other Pricelist.' ),
       'category_id': fields.many2one( 'product.pricelist.category', 'Category', help='Use this field to classify pricelist items. Category does not affect the resulting price in any way.'),
       'rounding_mode': fields.selection([('nearest','Nearest Value'),('up','Up'),('down','Down')], 'Rounding Mode', readonly=False, help='Allows you to decide what rounding method to use.'),
    }
    _defaults = {
        'rounding_mode': lambda *a: 'nearest',
    }

    _constraints = [
        (_check_base_item_rule, 'Sequence of base item should be gretater than current item.',[]),
    ]
    _sql_constraints = [
        ('sequence_contraint', 'unique(base_pricelist_id, sequence)', 'Item sequence could not be equal'),
    ]
 
product_pricelist_item()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

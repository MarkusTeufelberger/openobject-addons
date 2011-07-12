# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Santiago Argüeso Armesto$
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

"""Adds serial sequence by product"""

from osv import osv, fields
import pooler

_sequences_cache = {}

def get_default_seq_id_for_sn(cr, uid, seq_name = 'COD', seq_code = 'generic.stock.sn.serial'):
    """
    Get by default a sequence for active product.
    If the sequence not exists it creates.
    """
    pool = pooler.get_pool(cr.dbname)

    if not _sequences_cache.get(cr.dbname):
    	_sequences_cache[cr.dbname] = {}

    if _sequences_cache[cr.dbname].get(seq_name):
        return _sequences_cache[cr.dbname][seq_name]
    else:
        sequence_ids = pool.get('ir.sequence').search(cr, uid, [('code', '=', seq_code), ('name', '=', seq_name)])
        if sequence_ids:
            sequence_id = sequence_ids[0]
        else:
            #
            # Creamos una nueva secuencia
            #
            sequence_id = pool.get('ir.sequence').create(cr, uid, {
                'name': seq_name,
                'code': seq_code,
                'padding': 3,
                'prefix': "L%(doy)s%(y)s (" + seq_name,
                'suffix': ")"
            })

    _sequences_cache[cr.dbname][seq_name] = sequence_id

    return sequence_id


class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'sn_required':fields.boolean('Números de serie'),
        'sequence_sn_id':fields.many2one('ir.sequence', 'Serial number Seq.'),
    }

    _defaults = {
        'sn_required':lambda *a: False,        
        'sequence_sn_id': lambda x, y, z, c: x.pool.get('ir.sequence').search(y, z, [('code', '=', 'generic.stock.sn.serial')]) and x.pool.get('ir.sequence').search(y, z, [('code', '=', 'generic.stock.sn.serial')])[0] or False
    }

product_template()


class product_product(osv.osv):

    _inherit = "product.product"

    _columns = {
        'default_code' : fields.char('Code', size=64, required=True)
    }

    _defaults = {
        'default_code': lambda *a: "COD",
    }

    def create(self, cr, uid, vals, context={}):
        """
        Overwrites create method for creates sequence to serial numbers
        """
        vals['sequence_sn_id'] = get_default_seq_id_for_sn(cr, uid, seq_name=vals.get('default_code', 'COD'))
        product_id = super(product_product, self).create(cr, uid, vals, context=context)

        return product_id

product_product()

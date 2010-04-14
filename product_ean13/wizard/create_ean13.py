# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Ana Juaristi (http://openerpsite.com) All Rights Reserved.
#    $Id$
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

import wizard
import netsvc
import pooler
import string
import math

ean13_create_form = """<?xml version="1.0" encoding="utf-8"?>
<form string="Create ean13">
    <label string="Do you want to create ean13 barcode for the selected product? Remember you must set country code and your company correct code on ean13 sequence" />
</form>"""

ean13_create_fields = {}

def is_pair(x):
    return not x%2


def _createEan13(self, cr, uid, data, context):
    product_obj = pooler.get_pool(cr.dbname).get('product.product')
    sequence_obj = pooler.get_pool(cr.dbname).get('ir.sequence')

    for product in product_obj.browse(cr, uid, data['ids'], context=context):
        ref = sequence_obj.get(cr, uid, 'product.ean13')

        sum=0
        for i in range(12):
            if is_pair(i):
                sum += int(ref[i])
            else:
                sum += 3 * int(ref[i])
        new_ean_cc = int(math.ceil(sum / 10.0) * 10 - sum)
        new_ean = ref + str(new_ean_cc)
        vals = {'ean13': new_ean}
        product_obj.write(cr, uid, [product.id], vals)

    return {}


class create_ean13(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : ean13_create_form,
                    'fields' : ean13_create_fields,
                    'state' : [('end', 'Cancel'),('create', 'Create ean13') ]}
        },
        'create' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _createEan13,
                    'state' : 'end'}
        },
    }
create_ean13("product_ean13.create_ean13")

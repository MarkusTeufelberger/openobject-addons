# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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

from osv import fields,osv
from tools.translate import _

import base64
import netsvc

class product_import_csv_wizard(osv.osv_memory):
    _name = 'product.import.csv.wizard'

    _columns = {
        'file': fields.binary('File', required=True),
        'result': fields.text('Result'),
        'state': fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def importCSV(self, cr, uid, ids, data, context={}):
        """
        Import Values from CSV File in OpenERP
        CSV Mapping:
        - product_csv_product
        - product_csv_product_template
        """

        result = []
        logger = netsvc.Logger()

        #form values
        form = self.browse(cr, uid, ids[0])
        data = base64.b64decode(form.file)

        #check mapping product_csv. Match same name
        csv_ids = self.pool.get('csv.file').search(cr, uid, ['|',('name','=','product_csv_product'),('name','=','product_csv_product_template')])
        if len(csv_ids) != 2:
            raise osv.except_osv(_('Error !'),_('product_csv_product and product_csv_product_template not know in CSV Mapping! Desing it! See documentation product_csv module'))

        #save data CSV file
        csv_mapping = self.pool.get('csv.file').browse(cr, uid, csv_ids[0])
        if not csv_mapping.path[-1] == '/':
            path = '%s/%s' % (csv_mapping.path, csv_mapping.file)
        else:
            path = '%s/%s' % (csv_mapping.path, csv_mapping.file)
        f = open(path, 'w')
        f.write(data)
        f.close()

        #get values
        product_csv_ids = self.pool.get('csv.file').search(cr, uid, [('name','=','product_csv_product')])
        product_template_csv_ids = self.pool.get('csv.file').search(cr, uid, [('name','=','product_csv_product_template')])

        product_values = self.pool.get('csv.file').import_csv(cr, uid, product_csv_ids, context)
        product_template_values = self.pool.get('csv.file').import_csv(cr, uid, product_template_csv_ids, context)

        #get sku field
        product_sku_field_ids = self.pool.get('csv.file.field').search(cr, uid, [('file_id','=',product_csv_ids[0]),('sku','=',True)])
        if len(product_sku_field_ids) != 1:
            raise osv.except_osv(_('Error !'),_('There are not SKU Field available. Check it! See documentation product_csv module'))
        product_sku_field = self.pool.get('csv.file.field').browse(cr, uid, product_sku_field_ids[0])
        sku_field = product_sku_field.name

        # process values create/writte product.product
        i = 0
        for product_value in product_values:
            product_value.extend(product_template_values[i]) #merge two lists

            # convert {} values to write/create
            values = {}
            for e in product_value:
                for (k,v) in e.iteritems():
                    values[k] = v

            if sku_field in values:
                product_ids = self.pool.get('product.product').search(cr, uid, [(sku_field,'=',values[sku_field])])

                if len(product_ids) > 0:
                    try:
                        self.pool.get('product.product').write(cr, uid, product_ids, values)
                        message = _("Row %s. SKU %s write.") % (i, values[sku_field])
                    except:
                        message = _("Row %s. Error SKU %s.") % (i, values[sku_field])
                else:
                    try:
                        self.pool.get('product.product').create(cr, uid, values)
                        message = _("Row %s. SKU %s create.") % (i, values[sku_field])
                    except:
                        message = _("Row %s. Error SKU %s.") % (i, values[sku_field])
                logger.notifyChannel('Product CSV', netsvc.LOG_INFO, message)
                result.append(message)
            else:
                message = _("Row %s. SKU field %s not exists. Review configuration CSV File") % (i, sku_field)
                logger.notifyChannel('Product CSV', netsvc.LOG_ERROR, message)
                result.append(message)
            i = i +1

        #finish process
        values = {
            'state': 'done',
            'result': '\n'.join(result),
        }
        self.write(cr, uid, ids, values)

        return True

product_import_csv_wizard()

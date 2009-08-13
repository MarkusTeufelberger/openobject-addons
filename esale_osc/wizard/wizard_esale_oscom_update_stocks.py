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
<form string="Stock Update">
    <separator string="Stock succesfully updated" colspan="4" />
</form>'''

_export_done_fields = {}

def _do_export(self, cr, uid, data, context):
    self.pool = pooler.get_pool(cr.dbname)
    esale_web_obj = self.pool.get('esale.oscom.web')
    product_obj = self.pool.get('product.product')

    if data['model'] == 'ir.ui.menu':
        website_ids = esale_web_obj.search(cr, uid, [('active', '=', True)])
    else:
        website_ids = []
        website_not = []
        for id in data['ids']:
            exportable_website = esale_web_obj.search(cr, uid, [('id', '=', id), ('active', '=', True)])
            if exportable_website:
                website_ids.append(exportable_website[0])
            else:
                website_not.append(id)

        if len(website_not) > 0:
            raise wizard.except_wizard(_("Error"), _("You asked to synchronize to non-active OScommerce web shop: IDs %s") % website_not)

    for website_id in website_ids:
        website = esale_web_obj.browse(cr, uid, website_id)
        product_obj.oscom_update_stock(cr, uid, website, context=context)
    return {}

class wiz_esale_oscom_stocks(wizard.interface):

    states = { 'init' : { 'actions' : [_do_export],
                          'result' : { 'type' : 'form',
                                       'arch' : _export_done_form,
                                       'fields' : _export_done_fields,
                                       'state' : [('end', 'End')]
                                     }
                        }
              }

wiz_esale_oscom_stocks('esale.oscom.stocks');


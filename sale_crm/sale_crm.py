# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'section_id': fields.many2one('crm.case.section', 'Sales Team'),
        'categ_ids': fields.many2many('crm.case.categ', 'sale_order_category_rel', 'order_id', 'category_id', 'Categories', \
            domain="['|',('section_id','=',section_id),('section_id','=',False), ('object_id.model', '=', 'crm.lead')]")
    }

class crm_case_section(osv.osv):
    _inherit = 'crm.case.section'

    def _get_number_saleorder(self, cr, uid, ids, field_name, arg, context=None):
        return self.get_number_items(cr, uid, ids, 'sale.order', [('state','not in',('draft','sent','cancel'))], context=context)

    def _get_number_quotation(self, cr, uid, ids, field_name, arg, context=None):
        return self.get_number_items(cr, uid, ids, 'sale.order', [('state','in',('draft','sent','cancel'))], context=context)

    def _get_number_invoice(self, cr, uid, ids, field_name, arg, context=None):
        return self.get_number_items(cr, uid, ids, 'account.invoice', [('state','not in',('draft','cancel'))], context=context)

    _columns = {
        'number_saleorder': fields.function(_get_number_saleorder, type='integer',  readonly=True),
        'number_quotation': fields.function(_get_number_quotation, type='integer',  readonly=True),
        'number_invoice': fields.function(_get_number_invoice, type='integer',  readonly=True),
    }

class res_users(osv.Model):
    _inherit = 'res.users'
    _columns = {
        'default_section_id': fields.many2one('crm.case.section', 'Default Sales Team'),
    }

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'section_id': fields.many2one('crm.case.section', 'Sales Team'),
    }
    _defaults = {
        'section_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).default_section_id.id or False,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

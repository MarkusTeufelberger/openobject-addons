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

import wizard
import pooler
from osv import osv
from tools.translate import _

invoice_form = """<?xml version="1.0"?>
<form string="Create external delivery invoices">
    <separator colspan="4" string="Do you really want to create the external delivery invoice(s) ?" />
    <field name="grouped" />
</form>
"""

invoice_fields = {
    'grouped' : {'string':'Group the invoices', 'type':'boolean', 'default': lambda *a: False}
}


def _makeInvoices(self, cr, uid, data, context):
    """creates invoices for external delivery lines"""
    picking_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid)
    newinv = []
    #diccionario que guardará las facturas agrupadas
    invoices = {}
    for p in picking_obj.browse(cr, uid, data['ids']):
        if p.type not in ('in','out') and (p.purchase_id or p.sale_id):
            raise osv.except_osv(_('Error !'), _('Only you can create external delivery invoice to out or in pickings with sale or purchase orders respectively.'))
        
        #object that contents an instance of purchase.order os an instance of sale.order
        order = p.purchase_id or p.sale_id

        #diccionario que contendrá las líneas que se van a crear sin agrupación
        lines =  {}
        #recorremos los gastos externos
        for dl in p.freight_tbcollected_id:
            if not dl.invoice_id or dl.invoice_id.state == 'cancel':
                #buscamos la cuenta de gastos
                a = dl.carrier_id.product_id.product_tmpl_id.property_account_expense.id
                if not a:
                    a = dl.carrier_id.product_id.categ_id.property_account_expense_categ.id
                if not a:
                    raise osv.except_osv(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (dl.carrier_id.product_id.name, dl.carrier_id.product_id.id))

                fpos = order.fiscal_position or False
                a = pooler.get_pool(cr.dbname).get('account.fiscal.position').map_account(cr, uid, fpos, a)
                #valores para una nueva línea de factura
                line = (0, False, {
                                        'name': p.name + ": " + dl.name,
                                        'account_id': a,
                                        'price_unit': pooler.get_pool(cr.dbname).get('res.currency').compute(cr, uid, dl.currency_id.id, user.company_id.currency_id.id, dl.price, round=True) or 0.0,
                                        'quantity': 1,
                                        'product_id': dl.carrier_id.product_id.id,
                                        'uos_id': dl.carrier_id.product_id.uom_id.id or False,
                                        'invoice_line_tax_id': [(6, 0, [x.id for x in dl.carrier_id.product_id.taxes_id])],
                                        'account_analytic_id': dl.account_analytic_id and dl.account_analytic_id.id or False
                                    })
                #si hay que agrupar
                if data['form']['grouped']:
                    if dl.carrier_id.partner_id.id not in invoices:
                        invoices[dl.carrier_id.partner_id.id] = {}
                    if dl.id not in invoices[dl.carrier_id.partner_id.id]:
                        invoices[dl.carrier_id.partner_id.id][dl.id] = []
                    invoices[dl.carrier_id.partner_id.id][dl.id].append(line)
                else:
                    if dl.carrier_id.partner_id.id not in lines:
                        lines[dl.carrier_id.partner_id.id] = {}
                    if dl.id not in lines[dl.carrier_id.partner_id.id]:
                        lines[dl.carrier_id.partner_id.id][dl.id] = []
                    lines[dl.carrier_id.partner_id.id][dl.id].append(line)

                picking_obj.write(cr, uid, [p.id], {'external_delivery_invoiced': True})

        #si hay líneas de factura sin agrupación las creamos
        if lines:
            for line in lines:
                partner = pooler.get_pool(cr.dbname).get('res.partner').browse(cr, uid, line)
                a = partner.property_account_payable.id
                journal_ids = pooler.get_pool(cr.dbname).get('account.journal').search(cr, uid, [('type', '=','purchase')], limit=1)
                invoice_lines = []
                dlines = []

                for dline in lines[line]:
                    invoice_lines.extend(lines[line][dline])
                    dlines.append(dline)

                inv = {
                    'name': "External delivery: " + p.name,
                    'reference': p.origin or p.name,
                    'account_id': a,
                    'type': 'in_invoice',
                    'partner_id': partner.id,
                    'currency_id': user.company_id.currency_id.id,
                    'address_invoice_id': pooler.get_pool(cr.dbname).get('res.partner').address_get(cr, uid, [partner.id], ['invoice'])['invoice'],
                    'address_contact_id': pooler.get_pool(cr.dbname).get('res.partner').address_get(cr, uid, [partner.id], ['default'])['default'],
                    'journal_id': len(journal_ids) and journal_ids[0] or False,
                    'origin': p.name,
                    'invoice_line': invoice_lines,
                    'fiscal_position': partner.property_account_position.id,
                    'payment_term': partner.property_payment_term and partner.property_payment_term.id or False
                }
                inv_id = pooler.get_pool(cr.dbname).get('account.invoice').create(cr, uid, inv, {'type':'in_invoice'})
                newinv.append(inv_id)
                pooler.get_pool(cr.dbname).get('delivery.freight.tobe.collected').write(cr, uid, dlines, {'invoice_id': inv_id})
                pooler.get_pool(cr.dbname).get('account.invoice').button_compute(cr, uid, [inv_id], {'type':'in_invoice'}, set_total=True)

    #si hay agrupaciones
    if invoices:
        for line in invoices:
            partner = pooler.get_pool(cr.dbname).get('res.partner').browse(cr, uid, line)
            a = partner.property_account_payable.id
            journal_ids = pooler.get_pool(cr.dbname).get('account.journal').search(cr, uid, [('type', '=','purchase')], limit=1)
            invoice_lines = []
            dlines = []
            
            for dline in invoices[line]:
                invoice_lines.extend(invoices[line][dline])
                dlines.append(dline)

            inv = {
                'name': "EDI: " + partner.name,
                'reference': "P%dEDI" % (partner.id),
                'account_id': a,
                'type': 'in_invoice',
                'partner_id': partner.id,
                'currency_id': user.company_id.currency_id.id,
                'address_invoice_id': pooler.get_pool(cr.dbname).get('res.partner').address_get(cr, uid, [partner.id], ['invoice'])['invoice'],
                'address_contact_id': pooler.get_pool(cr.dbname).get('res.partner').address_get(cr, uid, [partner.id], ['default'])['default'],
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'origin': "GROUP%s" % partner.id,
                'invoice_line': invoice_lines,
                'fiscal_position': partner.property_account_position.id,
                'payment_term': partner.property_payment_term and partner.property_payment_term.id or False
            }
            inv_id = pooler.get_pool(cr.dbname).get('account.invoice').create(cr, uid, inv, {'type':'in_invoice'})
            newinv.append(inv_id)
            pooler.get_pool(cr.dbname).get('delivery.freight.tobe.collected').write(cr, uid, dlines, {'invoice_id': inv_id})
            pooler.get_pool(cr.dbname).get('account.invoice').button_compute(cr, uid, [inv_id], {'type':'in_invoice'}, set_total=True)

    pool = pooler.get_pool(cr.dbname)
    mod_obj = pool.get('ir.model.data')
    act_obj = pool.get('ir.actions.act_window')
    xml_id='action_invoice_tree8'
    result = mod_obj._get_id(cr, uid, 'account', xml_id)
    id = mod_obj.read(cr, uid, result, ['res_id'])['res_id']
    result = act_obj.read(cr, uid, id)
    result['domain'] ="[('id','in', ["+','.join(map(str,newinv))+"])]"
    return result

class make_external_delivery_invoice(wizard.interface):
    """creates a group or no group invoice for selected purchase orders"""

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : invoice_form,
                    'fields' : invoice_fields,
                    'state' : [('end', 'Cancel'),('invoice', 'Create invoices') ]}
        },
        'invoice' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _makeInvoices,
                    'state' : 'end'}
        },
    }

make_external_delivery_invoice("freight.tobe.collected.make_invoice")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


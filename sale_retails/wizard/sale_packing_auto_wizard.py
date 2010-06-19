# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_retails module for OpenERP, allows the management of deposit
#
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#
#    Copyright (C) 2010 SYLEAM Info Services (<http://www.syleam.fr/>) Suzanne Jean-Sebastien
#
#    This file is a part of sale_retails
#
#    sale_retails is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_retails is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import wizard
from osv import osv
import pooler
import netsvc

ARCH = '''<?xml version="1.0"?>
<form string="Make packing">
    <label string="Do you want make all the packing ?" colspan="4"/>
</form>'''


class sale_packing_auto(wizard.interface):

    def _is_already_packing(self, cr, uid, data, context=None):
        """
            check if the packing be made
        """
        if not context:
            context = {}
        # the packing be already made if the shipped is true
        sale_order_obj = pooler.get_pool(cr.dbname).get('sale.order')
        sale_order = sale_order_obj.browse(cr, uid, [data['id']], context)[0]
        shipped = sale_order.shipped
        if shipped:
            return 'sendsignal'
        return 'askpacking'
        

    def _make_packing(self, cr, uid, data, context=None):
        """
            force assigne to move and move the picking on the sale order
        """
        if not context:
            context = {}
        # reference of instance of workflow
        wkf_service = netsvc.LocalService('workflow')
        #we want get the picking on the sale_order
        sale_order_obj = pooler.get_pool(cr.dbname).get('sale.order')
        sale_order = sale_order_obj.browse(cr, uid, [data['id']], context)[0]
        picking_id = sale_order.picking_ids[0].id
        picking_obj = pooler.get_pool(cr.dbname).get('stock.picking')
        # force the the possibility to move and move the picking
        picking_obj.force_assign(cr, uid, [picking_id])
        picking_obj.action_move(cr, uid, [picking_id])
        #send signal to validate the picking
        wkf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)
        return {}
    
    
    def _send_manual_invoice_signal(self, cr, uid, data, context=None):
        """
            force assigne to move and move the picking on the sale order
        """
        if not context:
            context = {}
        # reference of instance of workflow
        wkf_service = netsvc.LocalService('workflow')
        #send signal to run the creation of invoice
        wkf_service.trg_validate(uid, data['model'], data['id'], 'manual_invoice', cr)
        return {}

    def _open_invoice(self, cr, uid, data, context):
        print "_open_invoice/data: %r" % data
        # get the invoice numbers
        sale_order = pooler.get_pool(cr.dbname).get('sale.order').browse(cr, uid, data['id'], context)
        invoice_numbers_ids = []
        for invoice in sale_order.invoice_ids:
            invoice_numbers_ids.append(invoice.id)
        pool_obj = pooler.get_pool(cr.dbname)
        model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),
            ('name','=','invoice_form')])
        resource_id = pool_obj.get('ir.model.data').read(cr,uid,model_data_ids,fields=['res_id'])[0]['res_id']
        return {
                'domain': "[('id','in', "+str(invoice_numbers_ids)+")]",
            'name': 'Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'views': [(False,'tree'),(resource_id,'form')],
            'type': 'ir.actions.act_window'
        }

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'choice',
                'next_state': _is_already_packing,
            },
        },
        'askpacking': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': ARCH,
                'fields': {},
                'state': [
                    ('sendsignal', 'Cancel', 'gtk-cancel'),
                    ('make', 'Ok', 'gtk-ok', True)
                ],
            },
        },
        'make': {
            'actions': [_make_packing],
            'result': {
                'type': 'state',
                'state':'sendsignal',
            },
        },
        'sendsignal': {
            'actions': [_send_manual_invoice_signal],
            'result': {
                'type': 'state',
                'state':'open',
            },
        },
        'open': {
            'actions': [],
            'result': {'type':'action', 'action':_open_invoice, 'state':'end'}
        },
    }

sale_packing_auto('sale_packing_auto')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

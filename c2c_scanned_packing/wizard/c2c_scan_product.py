 # -*- encoding: utf-8 -*-
 ##############################################################################
 #
 #    Copyright Camptocamp SA
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

import tools
import netsvc
from tools import to_xml
from osv import osv,fields
from tools.translate import _


def _to_xml(s):
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

class c2c_scan_product(osv.osv_memory):
    """Scan Packed Product"""
    _name = 'c2c.scan.product'
    _description = __doc__
    _columns = {
        'barcode': fields.char('Barcode ',size=13)
    }
    
    def default_get(self, cr, uid, fields, context):
        """ To get default values for the object.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values 
        @param context: A standard dictionary 
        @return: A dictionary which of fields with values. 
        """
        res = super(c2c_scan_product, self).default_get(cr, uid, fields, context=context)
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        picking = picking_obj.browse(cr, uid, context.get('record_id'))
        move_ids = move_obj.search(cr, uid, [('picking_id','=', picking.id)])
        for move in move_obj.browse(cr, uid, move_ids):
            if move.state in ('done', 'cancel'):
                continue
            quantity = move.product_qty - move.scan_qty
            if move.state<>'assigned':
                quantity = 0
            if ('move%s'%move.id) in fields:
                res.update({('move%s'%move.id): quantity})
        return res
        

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        """override fields_view_get method"""
        if not context:
            context= {}
        result = super(c2c_scan_product, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar=toolbar)
        picking = self.pool.get('stock.picking').browse(cr, uid, context.get('record_id', False))
        if picking.move_lines:
            arch_lst = ['<form string="Scan Product">', '<label colspan="4" string="Bar Code Scan" />']
            arch_lst.append('<field name="barcode" colspan="4" nolabel="1" default_focus="1"/>\n<newline />')
            arch_lst.append('<group col="3" colspan="4">')
            arch_lst.append('<button icon=\'gtk-cancel\' name="cancel_scan" type="object" string="Cancel" />')
            arch_lst.append('<button name="open_validate_partial_packing" string="Make Partial"  type="object" icon="gtk-go-forward" />')
            arch_lst.append('<button name="scan" string="Add Product"  type="object" icon="gtk-apply" default_focus="1"/>')
            arch_lst.append('<separator string="Remaining quantity to pack per product" colspan="4" />\n<newline />')
            for move in picking.move_lines:
                result['fields']['move%s' %move.id] = {'string' : _to_xml(move.name), 'type' : 'float', 'readonly':True}
                arch_lst.append('<field name="move%s" />\n<newline />' %move.id)
                if 'move%s'%(move.id) not in self._columns:
                    self._columns['move%s'%(move.id)] = fields.float(string=move.name)            
            arch_lst.append('</group>')
            arch_lst.append('</form>')
        result['arch'] = '\n'.join(arch_lst)
        return result
  
         
    def open_validate_partial_packing(self, cr, uid, ids, context):
        
        """Open validate partial packing wizard"""
        
        data_obj = self.pool.get('ir.model.data')
        validate_id2 = data_obj._get_id(cr, uid, 'c2c_scanned_packing', 'view_validate_partial_packing')
        if validate_id2:
            validate_id2 = data_obj.browse(cr, uid, validate_id2, context=context).res_id
    
        return {
            'name': _('Validate Partial Packing'), 
            'view_type': 'form', 
            'view_mode': 'form,tree', 
            'res_model': 'validate.partial.packing', 
            'view_id': False, 
            'views': [(validate_id2, 'form'), (False, 'tree'), (False, 'calendar'), (False, 'graph')], 
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True
        }
  
    def open_last_packing_msg(self, cr, uid, ids, context):
        
        """Open last packing msg"""
        
        data_obj = self.pool.get('ir.model.data')
        last_pack_id = data_obj._get_id(cr, uid, 'c2c_scanned_packing', 'view_last_packing_confirm')
        if last_pack_id:
            last_pack_id = data_obj.browse(cr, uid, last_pack_id, context=context).res_id
        return {
            'name': _('Last Packing Message'), 
            'view_type': 'form', 
            'view_mode': 'form', 
            'res_model': 'last.packing.confirm', 
            'view_id': False, 
            'views': [(last_pack_id, 'form'), (False, 'tree'), (False, 'calendar'), (False, 'graph')], 
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True
        }  
        
  
    def cancel_scan(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        picking = picking_obj.browse(cr, uid, context.get('record_id'))
        move_ids = move_obj.search(cr, uid, [('picking_id','=', picking.id)])
        for move in move_obj.browse(cr, uid, move_ids):
            move_obj.write(cr, uid, [move.id], {'scan_qty': 0.0})
        return {}
      
      
    def scan(self, cr, uid, ids, context=None):
        """ 
         To get the barcode and scan product         
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary 
         @return : retrun barcode
        """
        if not context:
            context = {}
        record_id = context and context.get('record_id',False)
        assert record_id, 'Active ID not found'
        product_obj=self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        validate_wiz_obj = self.pool.get('validate.partial.packing')
        picking = pick_obj.browse(cr, uid, context.get('record_id')) 
        prod_pak_obj = self.pool.get('product.packaging')       
        qty = False
        count = 0
        for data in self.read(cr, uid, ids):
            for k in data.iterkeys():
                if k.startswith('move') and data[k] != False:
                    count +=1 
            packaging_ids = prod_pak_obj.search(cr,uid, [('ean','=', data['barcode'])])
            if packaging_ids:
                for packaging in prod_pak_obj.browse(cr, uid, packaging_ids):
                    move_ids = move_obj.search(cr, uid, [('picking_id', '=', record_id), ('product_id', '=', packaging.product_id.id)])
                    if move_ids:               
                        for move in move_obj.browse(cr, uid, move_ids):
                           if data.get('move%s' %move.id, False):
                                if packaging.qty > move.product_qty:
                                         raise osv.except_osv(_('Warning!'),
                                                _('Packed Quantity is higher than Product quantity!!!!'))
                                else:
                                    quantity =  data['move%s' %move.id] - packaging.qty
                                    qty =  quantity
                                    if qty == 0:
                                        raise osv.except_osv(_('Warning!'),
                                                _('This Product is already completely packed!!!!'))
                                    if data.get('move%s' %move.id, False) == 1:
                                        if count == 1:    
                                            pack_done = self.open_last_packing_msg(cr, uid, ids, context)
                                            partial_pack = validate_wiz_obj.make_partial(cr, uid, ids, context=context)
                                            move_obj.write(cr, uid, [move.id], {'scan_qty': move.scan_qty + packaging.qty})
                                            return pack_done
                                        else:
                                            partial_pack = validate_wiz_obj.make_partial(cr, uid, ids, context=context)
                                            move_obj.write(cr, uid, [move.id], {'scan_qty': move.scan_qty + packaging.qty})
                                    else:
                                        move_obj.write(cr, uid, [move.id], {'scan_qty': move.scan_qty + packaging.qty })
            else:
                  product_ids = product_obj.search(cr, uid, [('ean13','=', data['barcode'])])
                  if not product_ids:
                        raise osv.except_osv(_('Warning!'),
                                _('EAN13 Code Unknown!!'))
                  for product in  product_obj.browse(cr, uid, product_ids):                                                                                                                
                      move_ids = move_obj.search(cr, uid, [('picking_id', '=', record_id), ('product_id', '=', product.id)])
                      if move_ids:
                          for move in move_obj.browse(cr, uid, move_ids):
                                if data.get('move%s' %move.id, False) == 1:
                                    if count == 1:
                                           pack_done = self.open_last_packing_msg(cr, uid, ids, context) 
                                           move_obj.write(cr, uid, [move.id], {'scan_qty': move.scan_qty +1})
                                           partial_pack = validate_wiz_obj.make_partial(cr, uid, ids, context=context)
                                           return pack_done
                                    else:                                           
                                        move_obj.write(cr, uid, [move.id], {'scan_qty': move.scan_qty +1})
                                        partial_pack = validate_wiz_obj.make_partial(cr, uid, ids, context=context)

                                else: 
                                    move_obj.write(cr, uid, [move.id], {'scan_qty': move.scan_qty +1})
                      else:
                            raise osv.except_osv(_('Warning!'),
                                    _('This Product is Not in list. Do not Pack it!!'))
        
        return {
            'name': _('Scan Product '), 
            'view_type': 'form', 
            'view_mode': 'form', 
            'res_model': 'c2c.scan.product', 
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True
        }
    
c2c_scan_product()

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
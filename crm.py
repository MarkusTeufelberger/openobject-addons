from osv import fields, osv
import tools
import ir
import pooler
from mx import DateTime

class crm_case(osv.osv):
    _inherit = "crm.case"
    _columns = {
        'rma_ref': fields.char('Incident Ref', size=64, required=True, select=1),
        'incoming_picking_id': fields.many2one('stock.picking', 'Incoming Picking', required=False, select=1),
        'outgoing_picking_id': fields.many2one('stock.picking', 'Outgoing Picking', required=False, select=True),
        'related_incoming_picking_state': fields.related('incoming_picking_id', 'state', type="char", string="Related Picking State", readonly=True),
        'related_outgoing_picking_state': fields.related('outgoing_picking_id', 'state', type="char", string="Related Picking State", readonly=True),
        'in_supplier_picking_id': fields.many2one('stock.picking', 'Return To Supplier Picking', required=False, select=True),
        'out_supplier_picking_id': fields.many2one('stock.picking', 'Return From Supplier Picking', required=False, select=True),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number'),
        'product_id': fields.many2one('product.product', 'Product'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
    }
    
    _defaults = {
        'rma_ref': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'rma'),
    }
         
        
crm_case()
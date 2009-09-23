from osv import fields, osv
import netsvc

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns={
                'company_id': fields.many2one('res.company','Company',required=True),
              }
purchase_order()  
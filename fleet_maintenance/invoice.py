# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from osv import fields,osv
from mx.DateTime import RelativeDateTime, DateTime
from mx import DateTime


fixed_month_init_day = 1 # TODO make this a parameter!
fixed_days_before_month_end = 0 #TODO make this a parameter!
min_maintenance_months = 6 #TODO make this a parameter!


class account_invoice(osv.osv):
   _inherit = "account.invoice"

   def _refund_cleanup_lines(self, cr, uid, lines):
       for line in lines:
           if 'fleet_id' in line:
               line['fleet_id'] = line.get('fleet_id', False) and line['fleet_id'][0]
           if 'account_analytic_lines' in line:
               line['account_analytic_lines'] = [(6,0, line.get('account_analytic_lines', [])) ]
       return super(account_invoice, self)._refund_cleanup_lines(cr, uid, lines)

account_invoice()


class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    def create(self, cr, uid, vals, context={}):
        """Prevents the ORM from trying to write the is_maintenance product fields view fields related.
        User might indeed not have this right, example is an accountant creating a credit note.
        Actually this looks like a bug in OpenObject because it will try to write even if we declared
        the is_maintenance field as read_only.
        see bugreport here https://bugs.launchpad.net/openobject-server/+bug/426676
        """
        if vals.get('is_maintenance', False):
            del(vals['is_maintenance'])
        if vals.get('account_analytic_lines', False):
            del(vals['account_analytic_lines'])
        return super(account_invoice_line, self).create(cr, uid, vals, context=context)  
    
    def copy(self, cr, uid, id, default=None, context={}):
        if not default:
            default = {}
        default['account_analytic_lines'] = False
        return super(account_invoice_line, self).copy(cr, uid, id, default, context=context)

    def _get_maintenance_month_qty_from_start_end(self, cr, uid, start, end):
        delta = DateTime.RelativeDateDiff(end + RelativeDateTime(days=fixed_days_before_month_end + 1), start)
        return delta.months + delta.years * 12
    
    def _maintenance_month_qty(self, cr, uid, ids, prop, unknow_none, context={}):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.maintenance_start_date and line.maintenance_end_date:
                result[line.id] = self._get_maintenance_month_qty_from_start_end(cr, uid, DateTime.strptime(line.maintenance_start_date, '%Y-%m-%d'), DateTime.strptime(line.maintenance_end_date, '%Y-%m-%d'))
            else:
                result[line.id] = False
        return result


    _columns = {
        'maintenance_month_qty': fields.function(_maintenance_month_qty, method=True, string="Maintenance Month Quantity", type='integer', store=True),
        'maintenance_product_qty': fields.float('Maintenance Product Quantity', required=False), 
        'fleet_id': fields.many2one('stock.location', 'Fleet'),
        'parent_fleet_id': fields.related('fleet_id', 'location_id', type='many2one', relation='stock.location', string='Fleet', store=True),
        'maintenance_start_date':fields.date('Maintenance Start Date', required = False),
        'maintenance_end_date':fields.date('Maintenance End Date', required = False),
        'is_maintenance': fields.related('product_id', 'is_maintenance', type='boolean', string='Is Maintenance'),
        'account_analytic_lines': fields.one2many('account.analytic.line', 'invoice_line_id', 'Analytic Lines'),
    }
        
account_invoice_line()

class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    
    _columns = {
        'invoice_line_id':fields.many2one('account.invoice.line', 'Invoice Line'),
        'invoice_id': fields.related('invoice_line_id', 'invoice_id', type='many2one', relation='account.invoice', string='Invoice', store=True, select=1),
    }
    
account_analytic_line()


class account_move_line(osv.osv):
    _inherit="account.move.line"

    def create_analytic_lines(self, cr, uid, ids, context={}):
        res = super(account_move_line, self).create_analytic_lines(cr, uid, ids, context)
        matched_invoice_line_ids = []
        for move_line in self.browse(cr, uid, ids, context):
            
            if move_line.analytic_lines and len(move_line.analytic_lines) == 1 and move_line.product_id.is_maintenance and move_line.invoice:
                print "native analytic line creation"
                print move_line
                analytic_line = move_line.analytic_lines[0] #we assume their is only one analytic line for a maintenance product
                print analytic_line
                
                for invoice_line in move_line.invoice.invoice_line:
                    if invoice_line.id not in matched_invoice_line_ids: #we take care of not matching invoice line twice
                        if invoice_line.product_id and invoice_line.product_id.is_maintenance \
                            and invoice_line.product_id.id == analytic_line.product_id.id and analytic_line.amount == invoice_line.price_subtotal:
                            matched_invoice_line_ids.append(invoice_line.id)
                            month_qty = int(invoice_line.maintenance_month_qty)
                            splitted_amount =  invoice_line.quantity / invoice_line.maintenance_month_qty
                            amount = float(analytic_line.amount) / float(invoice_line.maintenance_month_qty)
                            
                            start_date = DateTime.strptime(invoice_line.maintenance_start_date, '%Y-%m-%d')
                            
                            self.pool.get('account.analytic.line').write(cr, uid, analytic_line.id, {'invoice_line_id':invoice_line.id, 'date':start_date, 'unit_amount':splitted_amount, 'amount': amount})
                            
                            for i in range(1, month_qty):
                                start_date += DateTime.RelativeDateTime(months=1)
                                print start_date
                                self.pool.get('account.analytic.line').copy(cr, uid, analytic_line.id, {'date': start_date}) #TODO check month_qty
                
        return res
                

account_move_line()

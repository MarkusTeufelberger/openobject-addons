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

class report_commission_month(osv.osv):
    _name = "report.commission.month"
    _description = "Commission of month"
    _auto = False
    _columns = {
        'name': fields.char('Sales Agent Name',size=64, readonly=True),
        'sono': fields.integer('Sales Order No', readonly=True),
        'invno': fields.integer('Invoice Number', readonly=True),
        'product_quantity': fields.integer('Product Quantity', readonly=True),
        'productname': fields.char('Product Name',size=256, readonly=True),
        'inv_total': fields.float('Invoice Amount', readonly=True),
        'in_date': fields.date('Invoice Date', readonly=True),
        'comrate': fields.float('Commission Rate (%)', readonly=True),
        'commission': fields.float('Commissions Amount', readonly=True),
        'state': fields.char('Invoice State', size=64,readonly=True),
        'pdate': fields.date('Invoice Paid Date', readonly=True),

    }
    _order = 'name,sono,state'

    def init(self, cr):
        cr.execute(""" create or replace view report_commission_month as (select * from
        (select sg.id as id,sg.name as name,so.name as sono,ai.number as invno,
    al.quantity as product_quantity,al.name as productname,(al.quantity * al.price_unit) as inv_total,
    to_char(ai.date_invoice, 'YYYY-MM-DD') as in_date,
    ((1-pi.price_discount)*100) as comrate,((al.quantity *al.price_unit)*(1-pi.price_discount))
              as commission,ai.state,'' as pdate
from
account_invoice ai,
sale_order so,
account_invoice_line al,
res_partner p,
sale_agent sg,
product_pricelist_item pi,
product_pricelist_version pv

where ai.origin=so.name
and ai.state in ('draft','open','proforma','cancel')
and al.invoice_id=ai.id and p.id=ai.partner_id
and sg.id=p.agent_id and pi.price_version_id=pv.id

and sg.comprice_id = pv.pricelist_id and pi.price_discount > 0) as a

UNION

(
select min(A.id) as id,A.name as name,S.name as sono,I.number as invno
              ,L.quantity as product_quantity,L.name as productname,
              (L.quantity * L.price_unit) as inv_total,to_char(I.date_invoice, 'YYYY-MM-DD') as in_date,
              ((1-R.price_discount)*100) as comrate,((L.quantity * L.price_unit)*(1-R.price_discount))
              as commission,I.state,AMR.name as pdate from

sale_agent A,
account_move_reconcile AMR,
res_partner P,
account_invoice I,
product_pricelist_item R,
account_invoice_line L,
sale_order S,
product_pricelist_version PV

 where
I.state='paid' and
R.price_version_id=PV.id AND A.comprice_id = PV.pricelist_id AND I.origin=S.name AND
R.price_discount > 0 AND S.partner_id = P.id AND P.agent_id=A.id AND I.partner_id=P.id AND I.id=L.invoice_id
group by L.quantity, L.price_unit,R.price_discount,I.state,I.id,A.name,P.name,I.state,I.date_invoice,L.name,
S.name,I.number,A.id,AMR.name
)
) """)
report_commission_month()




class report_commission_month_rate(osv.osv):
    _name = "report.commission.month.rate"
    _description = "Commission of month rate"
    _auto = False
    _columns = {
        'name': fields.char('Sales Agent Name',size=64, readonly=True, select=True),
        'sono': fields.char('Sales Order No',size=64, readonly=True, select=True),
        'invno': fields.char('Invoice Number',size=64, readonly=True, select=True),
        'product_quantity': fields.integer('Product Quantity', readonly=True, select=True),
        'productname': fields.char('Product Name',size=256, readonly=True, select=True),
        'inv_total': fields.float('Invoice Amount', readonly=True, select=True),
        'in_date': fields.date('Invoice Date', readonly=True, select=True),
        'comrate': fields.float('Commission Rate (%)', readonly=True, select=True),
        'commission': fields.float('Commissions Amount', readonly=True, select=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Canceled')
        ],'Invoice State', select=True),
        'pdate': fields.date('Invoice Paid Date', readonly=True, select=True),

    }
    order = 'name,sono,state,productname'

    def init(self, cr):
        cr.execute("""
CREATE OR REPLACE VIEW report_commission_month_rate AS( select * from (select al.id AS id,
sg.name as name,
so.name as sono,
ai.number as invno,
al.quantity as product_quantity,
al.name as productname,
(al.quantity * al.price_unit) as inv_total,
to_char(ai.date_invoice, 'YYYY-MM-DD') as in_date,
sg.commission_rate as comrate,
(al.quantity *al.price_unit * sg.commission_rate / 100) as commission,
ai.state,
'' as pdate
from
account_invoice ai,
sale_order so,
account_invoice_line al,
res_partner p,
sale_agent sg

where ai.origin=so.name
and ai.state in ('draft','open','proforma','cancel')
and al.invoice_id=ai.id and p.id=ai.partner_id
and sg.id=p.agent_id


)
 as a

UNION

(

select al.id  AS id,
sg.name as name,
so.name as sono,
ai.number as invno,
al.quantity as product_quantity,
al.name as productname,
(al.quantity * al.price_unit) as inv_total,
to_char(ai.date_invoice, 'YYYY-MM-DD') as in_date,
sg.commission_rate as comrate,
(al.quantity *al.price_unit * sg.commission_rate / 100) as commission,
ai.state,
ar.name as pdate
from
account_invoice ai,
account_move am,
account_move_line aml,

account_move_reconcile ar,
sale_order so,
account_invoice_line al,
res_partner p,
sale_agent sg

where ai.origin=so.name
and ai.state in ('paid')
and al.invoice_id=ai.id and p.id=ai.partner_id
and sg.id=p.agent_id and ai.move_id=am.id
and aml.move_id=am.id
and ar.id = aml.reconcile_id

))""")
report_commission_month_rate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camtocamp SA
# @author Joël Grand-Guillaume
# $Id: $
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

from osv import fields,osv
from osv import orm
from tools.translate import _

class hr_analytic_timesheet(osv.osv):

    _inherit = "hr.analytic.timesheet"

    def on_change_account_id(self, cr, uid, ids, account_id, user_id=False, unit_amount=0):
        #{'value': {'to_invoice': False, 'amount': (-162.0,), 'product_id': 7, 'general_account_id': (5,)}}
        res = {}
        if not (account_id):
            #avoid a useless call to super
            return res 

        if not (user_id):
            return super(hr_analytic_timesheet, self).on_change_account_id(cr, uid, ids,account_id)

        #get the browse record related to user_id and account_id
        temp = self._get_related_user_account_recursiv(cr,uid,user_id,account_id)
        # temp = self.pool.get('analytic_user_funct_grid').search(cr, uid, [('user_id', '=', user_id),('account_id', '=', account_id) ])
        if not temp:
            #if there isn't any record for this user_id and account_id
            return super(hr_analytic_timesheet, self).on_change_account_id(cr, uid, ids,account_id)
        else:
            #get the old values from super and add the value from the new relation analytic_user_funct_grid
            r = self.pool.get('analytic_user_funct_grid').browse(cr, uid, temp)[0]
            res.setdefault('value',{})
            res['value']= super(hr_analytic_timesheet, self).on_change_account_id(cr, uid, ids,account_id)['value']
            res['value']['product_id'] = r.product_id.id
            res['value']['product_uom_id'] = r.product_id.product_tmpl_id.uom_id.id

            #the change of product has to impact the amount, uom and general_account_id
            a = r.product_id.product_tmpl_id.property_account_expense.id
            if not a:
                a = r.product_id.categ_id.property_account_expense_categ.id
            if not a:
                raise osv.except_osv(_('Error !'),
                        _('There is no expense account define ' \
                                'for this product: "%s" (id:%d)') % \
                                (r.product_id.name, r.product_id.id,))
             # Compute based on pricetype
            amount_unit=self.on_change_unit_amount(cr, uid, ids, 
               r.product_id.id, unit_amount, r.product_id.uom_id.id)['value']['amount']
               
            amount = unit_amount *  amount_unit
            res ['value']['amount']= - round(amount, 2)
            res ['value']['general_account_id']= a
        return res

    def on_change_user_id(self, cr, uid, ids,user_id, account_id, unit_amount=0):
        res = {}
        if not (user_id):
            #avoid a useless call to super
            return res 

        #get the old values from super
        res = super(hr_analytic_timesheet, self).on_change_user_id(cr, uid, ids,user_id,unit_amount)

        if account_id:
            #get the browse record related to user_id and account_id
            # temp = self.pool.get('analytic_user_funct_grid').search(cr, uid, [('user_id', '=', user_id),('account_id', '=', account_id) ])
            temp = self._get_related_user_account_recursiv(cr,uid,user_id,account_id)
            if temp:
                #add the value from the new relation analytic_user_funct_grid
                r = self.pool.get('analytic_user_funct_grid').browse(cr, uid, temp)[0]
                res['value']['product_id'] = r.product_id.id    

                #the change of product has to impact the amount, uom and general_account_id
                a = r.product_id.product_tmpl_id.property_account_expense.id
                if not a:
                    a = r.product_id.categ_id.property_account_expense_categ.id
                if not a:
                    raise osv.except_osv(_('Error !'),
                            _('There is no expense account define ' \
                                    'for this product: "%s" (id:%d)') % \
                                    (r.product_id.name, r.product_id.id,))
                # Compute based on pricetype
                amount_unit=self.on_change_unit_amount(cr, uid, ids, 
                        r.product_id.id, unit_amount, r.product_id.uom_id.id)['value']['amount']
                            
                amount = unit_amount * amount_unit
                res ['value']['amount']= - round(amount, 2)
                res ['value']['general_account_id']= a
        return res

hr_analytic_timesheet()


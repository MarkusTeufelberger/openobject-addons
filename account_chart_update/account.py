# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
import time
import netsvc

from osv import fields, osv

from tools.misc import currency
from tools.translate import _
from tools import config

class Log(Exception):
    def __init__(self):
        self.content = ""
        self.error = False
    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error
    def __call__(self):
        return self.content
    def __str__(self):
        return self.content

# Charts of Accounts update wizard
class wizard_update_charts_accounts(osv.osv_memory):
    """
    Updates an existing account chart for a company.
    Wizards ask for:
        * a company
        * an account chart template
        * a number of digits for formatting code of non-view accounts
    Then, the wizard:
        * generates/updates all accounts from the template and assigns them to the right company
        * generates/updates all taxes and tax codes, changing account assignations
        * generates/updates all accounting properties and assigns them correctly
    """
    _name='wizard.update.charts.accounts'

    _columns = {
        'state': fields.selection([
                ('one','Step 1'),
                ('two','Step 2'),
                ('done','Wizard Complete')
            ],'Status',readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'chart_template_id': fields.many2one('account.chart.template', 'Chart Template', required=True),
        'code_digits': fields.integer('# of Digits', required=True, help="No. of Digits to use for account code. Make sure it is the same number as existing accounts."),
        'update_tax_code': fields.boolean('Update tax codes', help="Existing tax codes are updated. Tax codes are searched by name."),
        'update_tax': fields.boolean('Update taxes', help="Existing taxes are updated. Taxes are searched by name."),
        'update_account': fields.boolean('Update accounts', help="Existing accounts are updated. Accounts are searched by code."),
        'update_fiscal_position': fields.boolean('Update fiscal positions', help="Existing fiscal positions are updated. Fiscal positions are searched by name."),
        'tax_code_ids': fields.one2many('wizard.update.charts.accounts.tax.code', 'update_chart_wizard_id', 'Tax codes'),
        'tax_ids': fields.one2many('wizard.update.charts.accounts.tax', 'update_chart_wizard_id', 'Taxes'),
        'account_ids': fields.one2many('wizard.update.charts.accounts.account', 'update_chart_wizard_id', 'Accounts'),
        'fiscal_position_ids': fields.one2many('wizard.update.charts.accounts.fiscal.position', 'update_chart_wizard_id', 'Fiscal positions'),
        'new_tax_code': fields.integer('Create - Tax codes', readonly=True),
        'new_tax': fields.integer('Create - Taxes', readonly=True),
        'new_account': fields.integer('Create - Accounts', readonly=True),
        'new_fp': fields.integer('Create - Fiscal positions', readonly=True),
        'updated_tax_code': fields.integer('Update - Tax codes', readonly=True),
        'updated_tax': fields.integer('Update - Taxes', readonly=True),
        'updated_account': fields.integer('Update - Accounts', readonly=True),
        'updated_fp': fields.integer('Update - Fiscal positions', readonly=True),
        'logs': fields.text('Logs', readonly=True)
    }

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        if not name:
            name = '%'
        if not args:
            args = []
        if not context:
            context = {}
        args = args[:]
        ids = []
        ids = self.search(cr, user, [('company_id', operator, name)]+ args, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        records = self.browse(cr, uid, ids, context)
        res = []
        for record in records:
            res.append((record.id, record.company_id.name+' - '+record.chart_template_id.name))
        return res

    def _get_chart(self, cr, uid, context=None):
        if context is None:
            context = {}
        ids = self.pool.get('account.chart.template').search(cr, uid, [], context=context)
        if ids:
            return ids[0]
        return False

    def _get_code_digits(self, cr, uid, context=None, company_id=None):
        """ To find out the number of digits of the company's accounts we look at the number of digits
            of the default receivable account of the company (or user's company if any company is given)"""
        if context is None:
            context = {}
        property_obj = self.pool.get('ir.property')
        account_obj = self.pool.get('account.account')
        if not company_id:
            user = self.pool.get('res.users').browse(cr, uid, uid, context)
            company_id = user.company_id.id
        property_ids = property_obj.search(cr, uid, [('name','=','property_account_receivable' ), ('company_id','=',company_id), ('res_id','=',False), ('value','!=',False)])
        number_digits = 6
        if property_ids:
            prop = property_obj.browse(cr, uid, property_ids[0], context=context)
            try:
                # OpenERP 5.0 and 5.2/6.0 revno <= 2236
                account_id = int(prop.value.split(',')[1])
            except AttributeError:
                # OpenERP 6.0 revno >= 2236
                account_id = prop.value_reference.id

            if account_id:
                code = account_obj.read(cr, uid, account_id, ['code'], context)['code']
                number_digits = len(code)
        return number_digits

    _defaults = {
        'state': lambda self, cr, uid, c: 'one',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr,uid,[uid],c)[0].company_id.id,
        'chart_template_id': _get_chart,
        'code_digits': _get_code_digits,
    }


    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = {'value': {
            'code_digits': self._get_code_digits(cr, uid, context=context, company_id=company_id),
            }
        }
        return res


    def action_one(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_multi = self.browse(cr, uid, ids[0])
        self.write(cr, uid, [obj_multi.id], {
            'state': 'one',
        }, context)
        return True


    def action_show(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_multi = self.browse(cr, uid, ids[0])
        obj_acc = self.pool.get('account.account')
        obj_acc_tax = self.pool.get('account.tax')
        obj_acc_template = self.pool.get('account.account.template')
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')
        obj_fiscal_position = self.pool.get('account.fiscal.position')

        # initial data
        obj_acc_root = obj_multi.chart_template_id.account_root_id
        tax_code_root_id = obj_multi.chart_template_id.tax_code_root_id.id
        company_id = obj_multi.company_id.id

        # counts
        new_tax_code = 0
        new_tax = 0
        new_account = 0
        new_fp = 0
        updated_tax_code = 0
        updated_tax = 0
        updated_account = 0
        updated_fp = 0

        # reset wizard tax codes, taxes, accounts and fiscal positions
        ids = self.pool.get('wizard.update.charts.accounts.tax.code').search(cr, uid, [])
        self.pool.get('wizard.update.charts.accounts.tax.code').unlink(cr, uid, ids)
        ids = self.pool.get('wizard.update.charts.accounts.tax').search(cr, uid, [])
        self.pool.get('wizard.update.charts.accounts.tax').unlink(cr, uid, ids)
        ids = self.pool.get('wizard.update.charts.accounts.account').search(cr, uid, [])
        self.pool.get('wizard.update.charts.accounts.account').unlink(cr, uid, ids)
        ids = self.pool.get('wizard.update.charts.accounts.fiscal.position').search(cr, uid, [])
        self.pool.get('wizard.update.charts.accounts.fiscal.position').unlink(cr, uid, ids)

        # tax codes
        children_tax_code_template = self.pool.get('account.tax.code.template').search(cr, uid, [('parent_id','child_of',[tax_code_root_id])], order='id')
        for tax_code_template in self.pool.get('account.tax.code.template').browse(cr, uid, children_tax_code_template):
            tax_code_name = (tax_code_root_id == tax_code_template.id) and obj_multi.company_id.name or tax_code_template.name
            ids = self.pool.get('account.tax.code').search(cr, uid, [('name','=',tax_code_name),('company_id','=',company_id)])
            id = ids and ids[0] or False
            if not id:
                new_tax_code += 1
                self.pool.get('wizard.update.charts.accounts.tax.code').create(cr, uid, {
                    'tax_code_id': tax_code_template.id,
                    'update_chart_wizard_id': obj_multi.id,
                }, context)
            elif obj_multi.update_tax_code:
                updated_tax_code += 1

        # taxes
        for tax in obj_multi.chart_template_id.tax_template_ids:
            ids = obj_acc_tax.search(cr, uid, [('name','=',tax.name),('company_id','=',company_id)])
            id = ids and ids[0] or False
            if not id:
                new_tax += 1
                self.pool.get('wizard.update.charts.accounts.tax').create(cr, uid, {
                    'tax_id': tax.id,
                    'update_chart_wizard_id': obj_multi.id,
                }, context)
            elif obj_multi.update_tax:
                updated_tax += 1

        # Accounts
        children_acc_template = obj_acc_template.search(cr, uid, [('parent_id','child_of',[obj_acc_root.id])])
        #children_acc_template.sort()
        for account_template in obj_acc_template.browse(cr, uid, children_acc_template):
            dig = obj_multi.code_digits
            code_main = account_template.code and len(account_template.code) or 0
            code_acc = account_template.code or ''
            if code_main>0 and code_main<=dig and account_template.type != 'view':
                code_acc=str(code_acc) + (str('0'*(dig-code_main)))
            ids = obj_acc.search(cr, uid, [('code','=',code_acc),('company_id','=',company_id)])
            id = ids and ids[0] or False
            if not id:
                new_account += 1
                self.pool.get('wizard.update.charts.accounts.account').create(cr, uid, {
                    'account_id': account_template.id,
                    'update_chart_wizard_id': obj_multi.id,
                }, context)
            elif obj_multi.update_account:
                updated_account += 1

        # Fiscal positions
        fp_ids = obj_fiscal_position_template.search(cr, uid,[('chart_template_id', '=', obj_multi.chart_template_id.id)])
        if fp_ids:
            for position in obj_fiscal_position_template.browse(cr, uid, fp_ids):
                ids = obj_fiscal_position.search(cr, uid, [('name','=',position.name),('company_id','=',company_id)])
                id = ids and ids[0] or False
                if not id:
                    new_fp += 1
                    self.pool.get('wizard.update.charts.accounts.fiscal.position').create(cr, uid, {
                        'fiscal_position_id': position.id,
                        'update_chart_wizard_id': obj_multi.id,
                    }, context)
                elif obj_multi.update_fiscal_position:
                    updated_fp += 1

        self.write(cr, uid, [obj_multi.id], {
            'state': 'two',
            'new_tax_code': new_tax_code,
            'new_tax': new_tax,
            'new_account': new_account,
            'new_fp': new_fp,
            'updated_tax_code': updated_tax_code,
            'updated_tax': updated_tax,
            'updated_account': updated_account,
            'updated_fp': updated_fp,
        }, context)
        return True


    def action_update(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_multi = self.browse(cr, uid, ids[0])
        obj_acc = self.pool.get('account.account')
        obj_acc_tax = self.pool.get('account.tax')
        obj_acc_template = self.pool.get('account.account.template')
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')
        obj_fiscal_position = self.pool.get('account.fiscal.position')
        obj_tax_fp = self.pool.get('account.fiscal.position.tax')
        obj_acc_fp = self.pool.get('account.fiscal.position.account')

        # initial data
        obj_acc_root = obj_multi.chart_template_id.account_root_id
        tax_code_root_id = obj_multi.chart_template_id.tax_code_root_id.id
        company_id = obj_multi.company_id.id
        tax_code_ids = [obj.tax_code_id.id for obj in obj_multi.tax_code_ids]
        tax_ids = [obj.tax_id.id for obj in obj_multi.tax_ids]
        account_ids = [obj.account_id.id for obj in obj_multi.account_ids]
        fiscal_position_ids = [obj.fiscal_position_id.id for obj in obj_multi.fiscal_position_ids]

        # new code
        acc_template_ref = {}
        tax_template_ref = {}
        tax_code_template_ref = {}
        todo_dict = {}

        # counts
        new_tax_code = 0
        new_tax = 0
        new_account = 0
        new_fp = 0
        updated_tax_code = 0
        updated_tax = 0
        updated_account = 0
        updated_fp = 0
        log = Log()

        # tax codes
        children_tax_code_template = self.pool.get('account.tax.code.template').search(cr, uid, [('parent_id','child_of',[tax_code_root_id])], order='id')
        for tax_code_template in self.pool.get('account.tax.code.template').browse(cr, uid, children_tax_code_template):
            tax_code_name = (tax_code_root_id == tax_code_template.id) and obj_multi.company_id.name or tax_code_template.name
            vals={
                'name': tax_code_name,
                'code': tax_code_template.code,
                'info': tax_code_template.info,
                'parent_id': tax_code_template.parent_id and ((tax_code_template.parent_id.id in tax_code_template_ref) and tax_code_template_ref[tax_code_template.parent_id.id]) or False,
                'company_id': company_id,
                'sign': tax_code_template.sign,
            }
            ids = self.pool.get('account.tax.code').search(cr, uid, [('name','=',tax_code_name),('company_id','=',company_id)])
            id = ids and ids[0] or False
            changed = False
            if not id:
                if tax_code_template.id in tax_code_ids:
                    new_tax_code += 1
                    changed = True
                    id = self.pool.get('account.tax.code').create(cr, uid, vals)
            elif obj_multi.update_tax_code:
                updated_tax_code += 1
                changed = True
                self.pool.get('account.tax.code').write(cr, uid, [id], vals)
            #recording the tax code to do the mapping
            tax_code_template_ref[tax_code_template.id] = id
            if changed and tax_code_template.parent_id and not ((tax_code_template.parent_id.id in tax_code_template_ref) and tax_code_template_ref[tax_code_template.parent_id.id]):
                log.add(_("Tax code %s: The parent tax code %s can not be set.\n") % (tax_code_name, tax_code_template.parent_id.name), False)

        # taxes
        for tax in obj_multi.chart_template_id.tax_template_ids:
            vals_tax = {
                'name':tax.name,
                'sequence': tax.sequence,
                'amount':tax.amount,
                'type':tax.type,
                'applicable_type': tax.applicable_type,
                'domain':tax.domain,
                'parent_id': tax.parent_id and ((tax.parent_id.id in tax_template_ref) and tax_template_ref[tax.parent_id.id]) or False,
                'child_depend': tax.child_depend,
                'python_compute': tax.python_compute,
                'python_compute_inv': tax.python_compute_inv,
                'python_applicable': tax.python_applicable,
                'tax_group':tax.tax_group,
                'base_code_id': tax.base_code_id and ((tax.base_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.base_code_id.id]) or False,
                'tax_code_id': tax.tax_code_id and ((tax.tax_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.tax_code_id.id]) or False,
                'base_sign': tax.base_sign,
                'tax_sign': tax.tax_sign,
                'ref_base_code_id': tax.ref_base_code_id and ((tax.ref_base_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.ref_base_code_id.id]) or False,
                'ref_tax_code_id': tax.ref_tax_code_id and ((tax.ref_tax_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.ref_tax_code_id.id]) or False,
                'ref_base_sign': tax.ref_base_sign,
                'ref_tax_sign': tax.ref_tax_sign,
                'include_base_amount': tax.include_base_amount,
                'description':tax.description,
                'company_id': company_id,
                'type_tax_use': tax.type_tax_use
            }
            ids = obj_acc_tax.search(cr, uid, [('name','=',tax.name),('company_id','=',company_id)])
            id = ids and ids[0] or False
            changed = False
            if not id:
                if tax.id in tax_ids:
                    new_tax += 1
                    changed = True
                    id = obj_acc_tax.create(cr, uid, vals_tax)
            elif obj_multi.update_tax:
                updated_tax += 1
                changed = True
                obj_acc_tax.write(cr, uid, [id], vals_tax)
            tax_template_ref[tax.id] = id
            if changed:
                #as the accounts have not been created yet, we have to wait before filling these fields
                todo_dict[id] = {
                    'account_collected_id': tax.account_collected_id and tax.account_collected_id.id or False,
                    'account_paid_id': tax.account_paid_id and tax.account_paid_id.id or False,
                }
                if tax.parent_id and not ((tax.parent_id.id in tax_template_ref) and tax_template_ref[tax.parent_id.id]):
                    log.add(_("Tax %s: The parent tax %s can not be set.\n") % (tax.name, tax.parent_id.name), False)
                if tax.base_code_id and not ((tax.base_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.base_code_id.id]):
                    log.add(_("Tax %s: The tax code for the base %s can not be set.\n") % (tax.name, tax.base_code_id.name), False)
                if tax.tax_code_id and not ((tax.tax_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.tax_code_id.id]):
                    log.add(_("Tax %s: The tax code for the tax %s can not be set.\n") % (tax.name, tax.tax_code_id.name), False)
                if tax.ref_base_code_id and not ((tax.ref_base_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.ref_base_code_id.id]):
                    log.add(_("Tax %s: The tax code for the base refund %s can not be set.\n") % (tax.name, tax.ref_base_code_id.name), False)
                if tax.ref_tax_code_id and not ((tax.ref_tax_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.ref_tax_code_id.id]):
                    log.add(_("Tax %s: The tax code for the tax refund %s can not be set.\n") % (tax.name, tax.ref_tax_code_id.name), False)

        #deactivate the parent_store functionnality on account_account for rapidity purpose
        self.pool._init = True

        # Accounts
        children_acc_template = obj_acc_template.search(cr, uid, [('parent_id','child_of',[obj_acc_root.id])])
        children_acc_template.sort()
        for account_template in obj_acc_template.browse(cr, uid, children_acc_template):
            tax_ids = [tax_template_ref[tax.id] for tax in account_template.tax_ids if tax_template_ref[tax.id]]
            dig = obj_multi.code_digits
            code_main = account_template.code and len(account_template.code) or 0
            code_acc = account_template.code or ''
            if code_main>0 and code_main<=dig and account_template.type != 'view':
                code_acc=str(code_acc) + (str('0'*(dig-code_main)))
            vals={
                'name': (obj_acc_root.id == account_template.id) and obj_multi.company_id.name or account_template.name,
                #'sign': account_template.sign,
                'currency_id': account_template.currency_id and account_template.currency_id.id or False,
                'code': code_acc,
                'type': account_template.type,
                'user_type': account_template.user_type and account_template.user_type.id or False,
                'reconcile': account_template.reconcile,
                'shortcut': account_template.shortcut,
                'note': account_template.note,
                'parent_id': account_template.parent_id and ((account_template.parent_id.id in acc_template_ref) and acc_template_ref[account_template.parent_id.id]) or False,
                'tax_ids': [(6,0,tax_ids)],
                'company_id': company_id,
            }
            ids = obj_acc.search(cr, uid, [('code','=',code_acc),('company_id','=',company_id)])
            id = ids and ids[0] or False
            changed = False
            if not id:
                if account_template.id in account_ids:
                    new_account += 1
                    changed = True
                    id = obj_acc.create(cr, uid, vals)
            elif obj_multi.update_account:
                updated_account += 1
                changed = True
                obj_acc.write(cr, uid, [id], vals)
            acc_template_ref[account_template.id] = id
            if changed and account_template.parent_id and not ((account_template.parent_id.id in acc_template_ref) and acc_template_ref[account_template.parent_id.id]):
                log.add(_("Account %s: The parent account %s can not be set.\n") % (code_acc, account_template.parent_id.code), False)

        #reactivate the parent_store functionnality on account_account
        self.pool._init = False
        self.pool.get('account.account')._parent_store_compute(cr)

        for key,value in todo_dict.items():
            if value['account_collected_id'] or value['account_paid_id']:
                if acc_template_ref[value['account_collected_id']] and acc_template_ref[value['account_paid_id']]:
                    obj_acc_tax.write(cr, uid, [key], vals={
                        'account_collected_id': acc_template_ref[value['account_collected_id']],
                        'account_paid_id': acc_template_ref[value['account_paid_id']],
                    })
                else:
                    tax = obj_acc_tax.browse(cr, uid, key)
                    if not (value['account_collected_id'] in acc_template_ref and acc_template_ref[value['account_collected_id']]):
                        log.add(_("Tax %s: The collected account can not be set.\n") % (tax.name), False)              
                    if not (value['account_paid_id'] in acc_template_ref and acc_template_ref[value['account_paid_id']]):
                        log.add(_("Tax %s: The paid account can not be set.\n") % (tax.name), False)              
                    
        # Fiscal positions
        fp_ids = obj_fiscal_position_template.search(cr, uid,[('chart_template_id', '=', obj_multi.chart_template_id.id)])
        if fp_ids:
            for position in obj_fiscal_position_template.browse(cr, uid, fp_ids):
                ids = obj_fiscal_position.search(cr, uid, [('name','=',position.name),('company_id','=',company_id)])
                id = ids and ids[0] or False
                changed = False
                if not id:
                    if position.id in fiscal_position_ids:
                        new_fp += 1
                        changed = True
                        vals_fp = {
                           'company_id' : company_id,
                           'name' : position.name,
                           }
                        id = obj_fiscal_position.create(cr, uid, vals_fp)
                elif obj_multi.update_fiscal_position:
                    updated_fp += 1
                    changed = True
                    ids = obj_tax_fp.search(cr, uid, [('position_id','=',id)])
                    obj_tax_fp.unlink(cr, uid, ids)
                    ids = obj_acc_fp.search(cr, uid, [('position_id','=',id)])
                    obj_acc_fp.unlink(cr, uid, ids)
                if changed:
                    for tax in position.tax_ids:
                        vals_tax = {
                                    'tax_src_id' : tax_template_ref[tax.tax_src_id.id],
                                    'tax_dest_id' : tax.tax_dest_id and tax_template_ref[tax.tax_dest_id.id] or False,
                                    'position_id' : id,
                                    }
                        obj_tax_fp.create(cr, uid, vals_tax)
                        if not ((tax.tax_src_id.id in tax_template_ref) and tax_template_ref[tax.tax_src_id.id]):
                            log.add(_("Fiscal position %s: The source tax %s can not be set.\n") % (position.name, tax.tax_src_id.name), False)
                        if tax.tax_dest_id and not ((tax.tax_dest_id.id in tax_template_ref) and tax_template_ref[tax.tax_dest_id.id]):
                            log.add(_("Fiscal position %s: The destination tax %s can not be set.\n") % (position.name, tax.tax_dest_id.name), False)
                    for acc in position.account_ids:
                        vals_acc = {
                                    'account_src_id' : acc_template_ref[acc.account_src_id.id],
                                    'account_dest_id' : acc_template_ref[acc.account_dest_id.id],
                                    'position_id' : id,
                                    }
                        obj_acc_fp.create(cr, uid, vals_acc)
                        if not ((acc.account_src_id.id in acc_template_ref) and acc_template_ref[acc.account_src_id.id]):
                            log.add(_("Fiscal position %s: The source account %s can not be set.\n") % (position.name, acc.account_src_id.code), False)
                        if not ((acc.account_dest_id.id in acc_template_ref) and acc_template_ref[acc.account_dest_id.id]):
                            log.add(_("Fiscal position %s: The destination account %s can not be set.\n") % (position.name, acc.account_dest_id.code), False)
                    

        self.write(cr, uid, [obj_multi.id], {
            'state': 'done',
            'new_tax_code': new_tax_code,
            'new_tax': new_tax,
            'new_account': new_account,
            'new_fp': new_fp,
            'updated_tax_code': updated_tax_code,
            'updated_tax': updated_tax,
            'updated_account': updated_account,
            'updated_fp': updated_fp,
            'logs': log(),
        }, context)
        return True
#        return {'type':'ir.actions.act_window_close' }

wizard_update_charts_accounts()


class wizard_update_charts_accounts_tax_code(osv.osv_memory):
    _name = 'wizard.update.charts.accounts.tax.code'

    _columns = {
        'tax_code_id': fields.many2one('account.tax.code.template', 'Tax codes', required=True),
        'update_chart_wizard_id': fields.many2one('wizard.update.charts.accounts', 'Update chart wizard', required=True),
    }

wizard_update_charts_accounts_tax_code()


class wizard_update_charts_accounts_tax(osv.osv_memory):
    _name = 'wizard.update.charts.accounts.tax'

    _columns = {
        'tax_id': fields.many2one('account.tax.template', 'Taxes', required=True),
        'update_chart_wizard_id': fields.many2one('wizard.update.charts.accounts', 'Update chart wizard', required=True),
    }

wizard_update_charts_accounts_tax()


class wizard_update_charts_accounts_account(osv.osv_memory):
    _name = 'wizard.update.charts.accounts.account'

    _columns = {
        'account_id': fields.many2one('account.account.template', 'Accounts', required=True),
        'update_chart_wizard_id': fields.many2one('wizard.update.charts.accounts', 'Update chart wizard', required=True),
    }

wizard_update_charts_accounts_account()


class wizard_update_charts_accounts_fiscal_position(osv.osv_memory):
    _name = 'wizard.update.charts.accounts.fiscal.position'

    _columns = {
        'fiscal_position_id': fields.many2one('account.fiscal.position.template', 'Fiscal positions', required=True),
        'update_chart_wizard_id': fields.many2one('wizard.update.charts.accounts', 'Update chart wizard', required=True),
    }

wizard_update_charts_accounts_fiscal_position()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


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

import pooler
import time
import datetime
import wizard
import netsvc
import base64
from osv import osv
from tools.translate import _

codawiz_form = """<?xml version="1.0"?>
<form string="Import Coda Statement">
<separator colspan="4" string="Select your bank journal :" />
    <field name="journal_id" colspan="1" domain="[('type','=','cash')]" />
    <newline />
    <field name="def_payable" />    <field name="def_receivable" />
    <newline />
    <field name="awaiting_account" />
    <separator string="Clic on 'New' to select your file :" colspan="4"/>
    <field name="coda"/>
</form>
"""

codawiz_fields = {
    'journal_id' : {
        'string':'Bank Journal',
        'type':'many2one',
        'relation':'account.journal',
        'required':True,

    },
    'coda' : {
        'string':'Coda File',
        'type':'binary',
        'required':True,
    },
    'def_payable' : {
        'string' : 'Default Payable Account',
        'type' : 'many2one',
        'relation': 'account.account',
        'required':True,
        'domain':[('type','=','payable')],
    },
    'def_receivable' : {
        'string' : 'Default receivable Account',
        'type' : 'many2one',
        'relation': 'account.account',
        'required':True,
        'domain':[('type','=','receivable')],
    },
    'awaiting_account' : {
        'string' : 'Default Account for Unrecognized Movement',
        'type' : 'many2one',
        'relation': 'account.account',
        'required':True,
    }

}

result_form = """<?xml version="1.0"?>
<form string="Import Coda Statement">
<separator colspan="4" string="Results :" />
    <field name="note" colspan="4" nolabel="1" width="500"/>
</form>
"""

result_fields = {

    'note' : {'string':'Log','type':'text'}

}


def _coda_parsing(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    codafile = data['form']['coda']
    jur_id = data['form']['journal_id']
    def_pay_acc = data['form']['def_payable']
    def_rec_acc = data['form']['def_receivable']

    str_log = ""
    err_log = "Errors:\n------\n"
    nb_err=0
    std_log=''
    str_log1 = "Coda File is Imported  :  "
    str_not=''
    str_not1=''

    bank_statement={}
    bank_statement_lines={}
    bank_statements=[]
    recordlist = base64.decodestring(codafile).split('\n')#remove \r by dhaval
    recordlist.pop()
    for line in recordlist:
        if line[0] == '0':
            # header data
            bank_statement["bank_statement_line"]={}
            bank_statement['date'] = str2date(line[5:11])
            bank_statement['journal_id']=data['form']['journal_id']
            period_id = pool.get('account.period').search(cr,uid,[('date_start','<=',time.strftime('%Y-%m-%d',time.strptime(bank_statement['date'],"%y/%m/%d"))),('date_stop','>=',time.strftime('%Y-%m-%d',time.strptime(bank_statement['date'],"%y/%m/%d")))])
            bank_statement['period_id'] = period_id[0]
            bank_statement['state']='draft'
        elif line[0] == '1':
            # old balance data
            bal_start = list2float(line[43:58])
            if line[42] == '1':
                bal_start = - bal_start
            bank_statement["balance_start"]= bal_start
            bank_statement["acc_number"]=line[5:17]
            bank_statement["acc_holder"]=line[64:90]

        elif line[0]=='2':
            # movement data record 2
            if line[1]=='1':
                # movement data record 2.1
                if bank_statement_lines.has_key(line[2:6]):
                    continue
                st_line = {}
                st_line['extra_note'] = ''
                st_line['statement_id']=0
                st_line['ref'] = line[2:10]
                st_line['date'] = time.strftime('%Y-%m-%d',time.strptime(str2date(line[115:121]),"%y/%m/%d")),
                st_line_amt = list2float(line[32:47])

                if line[61]=='1':
                    st_line['name']=line[65:77]
                else:
                    st_line['name']=line[62:115]

                st_line['free_comm'] = st_line['name']
                st_line['val_date']=time.strftime('%Y-%m-%d',time.strptime(str2date(line[47:53]),"%y/%m/%d")),
                st_line['entry_date']=time.strftime('%Y-%m-%d',time.strptime(str2date(line[115:121]),"%y/%m/%d")),
                st_line['partner_id']=0
                if line[31] == '1':
                    st_line_amt = - st_line_amt
                    st_line['account_id'] = def_pay_acc
                else:
                    st_line['account_id'] = def_rec_acc
                st_line['amount'] = st_line_amt
                bank_statement_lines[line[2:6]]=st_line
                bank_statement["bank_statement_line"]=bank_statement_lines
            elif line[1] == '2':
                st_line_name = line[2:6]
                bank_statement_lines[st_line_name].update({'account_id': data['form']['awaiting_account']})

            elif line[1] == '3':
                # movement data record 3.1
                st_line_name = line[2:6]
                st_line_partner_acc = str(line[10:47]).strip()
                cntry_number=line[10:47].strip()
                contry_name=line[47:125].strip()
                bank_ids = pool.get('res.partner.bank').search(cr,uid,[('acc_number','=',st_line_partner_acc)])
                bank_statement_lines[st_line_name].update({'cntry_number': cntry_number, 'contry_name': contry_name})
                if bank_ids:
                    bank = pool.get('res.partner.bank').browse(cr,uid,bank_ids[0],context)
                    if line and bank.partner_id:
                        bank_statement_lines[st_line_name].update({'partner_id': bank.partner_id.id})
                        if bank_statement_lines[st_line_name]['amount'] < 0 :
                            bank_statement_lines[st_line_name].update({'account_id': bank.partner_id.property_account_payable.id})
                        else :
                            bank_statement_lines[st_line_name].update({'account_id': bank.partner_id.property_account_receivable.id})
                else:
                    nb_err += 1
                    err_log += _('The bank account %s is not defined for the partner %s.\n')%(cntry_number,contry_name)
                    bank_statement_lines[st_line_name].update({'account_id': data['form']['awaiting_account']})

                bank_statement["bank_statement_line"]=bank_statement_lines
        elif line[0]=='3':
            if line[1] == '1':
                st_line_name = line[2:6]
                bank_statement_lines[st_line_name]['extra_note'] += line[40:113]
            elif line[1] == '2':
                st_line_name = line[2:6]
                bank_statement_lines[st_line_name]['extra_note'] += line[10:115]
            elif line[1] == '3':
                st_line_name = line[2:6]
                bank_statement_lines[st_line_name]['extra_note'] += line[10:100]
        elif line[0]=='8':
            # new balance record
            bal_end = list2float(line[42:57])
            if line[41] == '1':
                bal_end = - bal_end
            bank_statement["balance_end_real"]= bal_end

        elif line[0]=='9':
            # footer record
            bank_statements.append(bank_statement)
    #end for
    bkst_list=[]

    for statement in bank_statements:
        try:
            bk_st_id = pool.get('account.bank.statement').create(cr,uid,{
                'journal_id': statement['journal_id'],
                'date':time.strftime('%Y-%m-%d',time.strptime(statement['date'],"%y/%m/%d")),
                'period_id':statement['period_id'],
                'balance_start': statement["balance_start"],
                'balance_end_real': statement["balance_end_real"],
                'state':'draft',
            })
            lines=statement["bank_statement_line"]
            for value in lines:
                line=lines[value]
                reconcile_id = False
                rec_id = pool.get('account.move.line').search(cr, uid, [('name','=',line['name']),('account_id.reconcile','=',True)])
                if rec_id:
                    reconcile_id = pool.get('account.bank.statement.reconcile').create(cr, uid, {
                        'line_ids': [(6, 0, rec_id)]
                        }, context=context)
                str_not1 = ''
                if line['partner_id'] == 0:
                    nb_err+=1
                    err_log += '\nThe bank account %s is not defined for the partner %s.'%(cntry_number,contry_name)
                if line.has_key('contry_name') and line.has_key('cntry_number'):
                    str_not1="Partner name:%s \n Partner Account Number:%s \n Communication:%s \n Value Date:%s \n Entry Date:%s \n"%(line["contry_name"],line["cntry_number"],line["free_comm"]+line['extra_note'],line["val_date"][0],line["entry_date"][0])
                id=pool.get('account.bank.statement.line').create(cr,uid,{
                           'name':line['name'],
                           'date': line['date'],
                           'amount': line['amount'],
                           'partner_id':line['partner_id'] or 0,
                           'account_id':line['account_id'],
                           'statement_id': bk_st_id,
                           'reconcile_id': reconcile_id,
                           'note':str_not1,
                           'ref':line['ref'],
                           })
            cr.commit()

            str_not= "\n \n Account Number: %s \n Account Holder Name: %s " %(statement["acc_number"],statement["acc_holder"])
            std_log = std_log + "\nDate  : %s, Starting Balance :  %.2f , Ending Balance : %.2f \n"\
                      %(statement['date'], float(statement["balance_start"]), float(statement["balance_end_real"]))
            bkst_list.append(bk_st_id)

        except osv.except_osv, e:
            cr.rollback()
            nb_err+=1
            err_log= err_log +'\n Application Error : ' + str(e)
            raise # REMOVEME

        except Exception, e:
            cr.rollback()
            nb_err+=1
            err_log= err_log +'\n System Error : '+str(e)
            raise # REMOVEME
        except :
            cr.rollback()
            nb_err+=1
            err_log= err_log +'\n Unknown Error'
            raise

    err_log= err_log + '\n\nNumber of statements : '+ str(len([bkst_list]))
    err_log= err_log + '\nNumber of error :'+ str(nb_err) +'\n'

    pool.get('account.coda').create(cr, uid,{
        'name':codafile,
        'statement_id':bk_st_id,
        'note':str_log1+str_not+std_log+err_log,
        'journal_id':data['form']['journal_id'],
        'date':time.strftime("%Y-%m-%d"),
        'user_id':uid,
        })

    return {'note':str_log1 + std_log + err_log ,'journal_id': data['form']['journal_id'], 'coda': data['form']['coda'],'statment_id':bk_st_id}


def str2date(date_str):
            return time.strftime("%y/%m/%d",time.strptime(date_str,"%d%m%y"))

def str2float(str):
    try:
        return float(str)
    except:
        return 0.0

def list2str(lst):
            return str(lst).strip('[]').replace(',','').replace('\'','')

def list2float(lst):
            try:
                return str2float((lambda s : s[:-3] + '.' + s[-3:])(lst))
            except:
                return 0.0
def _import_data(self, cr, uid, data, context):
    data['form']['journal_id'] = 3
    data['form']['def_payable']=5
    data['form']['def_receivable']=10
    return data['form']
    domain = "[('user_id', '=', uid)]"

class coda_import(wizard.interface):
    def _action_open_window(self, cr, uid, data, context):
        form=data['form']
        return {
            'domain':"[('id','=',%d)]"%(form['statment_id']),
            'name': 'Statement',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.bank.statement',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id':form['statment_id'],
        }
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : codawiz_form,
                    'fields' : codawiz_fields,
                    'state' : [('end', '_Close'),('extraction', '_Ok') ]}
        },
        'extraction' : {
            'actions' : [_coda_parsing],
            'result' : {'type' : 'form',
                    'arch' : result_form,
                    'fields' : result_fields,
                    'state' : [('end', '_Close'),('open', '_Open Statement')]}
        },
        'open': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state': 'end'}

            },

    }
coda_import("account.coda_import")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

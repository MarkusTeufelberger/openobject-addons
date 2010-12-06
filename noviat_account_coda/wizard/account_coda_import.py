# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2010 Noviat nv/sa (www.noviat.be). All rights reserved.
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
import pooler
import time
import datetime
import wizard
import netsvc
import base64
from tools.translate import _
from osv import osv
logger=netsvc.Logger()

codawiz_form = """<?xml version="1.0"?>
<form string="Import CODA File">
<separator colspan="4" string="Select Details" />
    <field name="def_payable" />
    <newline />
    <field name="def_receivable" />
    <separator string="Select your file :" colspan="4"/>
    <field name="coda_data" filename="coda_fname"/>
    <newline />
    <field name="coda_fname"/>
</form>
"""

codawiz_fields = {
    'coda_data' : {
        'string':'CODA File',
        'type':'binary',
        'required':True,
    },
    'coda_fname' : {
        'string':'CODA Filename',
        'type':'char',
        'size': 128,
        'required':True,
        'default': lambda *a: '',
    },
    'def_payable' : {
        'string' : 'Default Payable Account',
        'type' : 'many2one',
        'relation': 'account.account',
        'required':True,
        'domain':[('type','=','payable')],
    },
    'def_receivable' : {
        'string' : 'Default Receivable Account',
        'type' : 'many2one',
        'relation': 'account.account',
        'required':True,
        'domain':[('type','=','receivable')],
    }
}

result_form = """<?xml version="1.0"?>
<form string="Import CODA File">
<separator colspan="4" string="Results :" />
    <field name="note" colspan="4" nolabel="1" width="500" height="400"/>
</form>
"""

result_fields = {
    'note' : {'string':'Log','type':'text'}
}

def _coda_parsing(self, cr, uid, data, context):

    pool = pooler.get_pool(cr.dbname)
    codafile = data['form']['coda_data']
    codafilename = data['form']['coda_fname']
    def_pay_acc = data['form']['def_payable']
    def_rec_acc = data['form']['def_receivable']

    journal_obj = pool.get('account.journal')
    trans_type_obj = pool.get('account.coda.trans.type')
    trans_code_obj = pool.get('account.coda.trans.code')
    trans_category_obj = pool.get('account.coda.trans.category')
    comm_type_obj = pool.get('account.coda.comm.type')
    err_log = ''
    bank_statements = []
    recordlist = base64.decodestring(codafile).split('\n')
    for line in recordlist:
        
        if not line:
            pass
        elif line[0] == '0':
            # start of a new statement within the CODA file
            bank_statement = {}
            bank_statement_lines = {}
            st_line_seq = 0
            glob_lvl_stack = [0]
            # header data
            if line[127] == '1':
                raise wizard.except_wizard(_('Data Error!'),
                    _('CODA V1 statements are not supported, please contact your bank!'))
            bank_statement['bank_statement_lines'] = {}
            bank_statement['date'] = str2date(line[5:11])
            period_id = pool.get('account.period').search(cr , uid, [('date_start' ,'<=', bank_statement['date']), ('date_stop','>=',bank_statement['date'])])
            if not period_id:
                raise wizard.except_wizard(_('Data Error!'), 
                    _("The CODA creation date doesn't fall within a predefined period!"))
            bank_statement['period_id'] = period_id[0]
            bank_statement['state'] = 'draft'
            
        elif line[0] == '1':
            if line[1] == '0':      # Belgian bank account BBAN structure
                raise wizard.except_wizard(_('Data Error!'),
                    _('Belgian bank accounts with BBAN structure are not supported !'))
                bank_statement['acc_number'] = line[5:17]
                if line[18:21] <> 'EUR':
                    raise wizard.except_wizard(_('Data Error!'),
                        _('only bank accounts in EUR are supported !'))                
            elif line[1] == '1':    # foreign bank account BBAN structure
                raise wizard.except_wizard(_('Data Error!'),
                    _('Foreign bank accounts with BBAN structure are not supported !'))
            elif line[1] == '2':    # Belgian bank account IBAN structure
                bank_statement['acc_number']=line[5:21] 
                journal_obj_ids = journal_obj.search(cr , uid, [('iban' ,'=', bank_statement['acc_number'])]) 
                if journal_obj_ids:
                    bank_statement['journal_id'] = journal_obj.browse(cr, uid, journal_obj_ids[0], context).id
                else:
                    raise wizard.except_wizard(_('Data Error!'),
                        _("No matching Financial Journal found !") +
                        _("\nPlease check if the IBAN field of your Bank Journal matches with '%s' !") % bank_statement['acc_number'])
                if line[39:42] <> 'EUR':
                    raise wizard.except_wizard(_('Data Error!'),
                        _('only bank accounts in EUR are supported !'))
            elif line[1] == '3':    # foreign bank account IBAN structure
                raise wizard.except_wizard(_('Data Error!'),
                     _('Foreign bank accounts with IBAN structure are not supported !'))
            else:
                raise wizard.except_wizard(('Data Error!'),
                     _('Unsupported bank account structure !'))                          
            bal_start = list2float(line[43:58])             # old balance data
            if line[42] == '1':    # 1= Debit
                bal_start = - bal_start
            bank_statement['balance_start'] = bal_start            
            bank_statement['acc_holder'] = line[64:90]
            bank_statement['coda_seq_number'] = line[125:128]

        elif line[0] == '2':
            # movement data record 2
            if line[1] == '1':
                # movement data record 2.1
                st_line = {}
                st_line_seq = st_line_seq + 1
                st_line['sequence'] = st_line_seq
                st_line['type'] = 'general'                
                st_line['struct_comm_type'] = ''
                st_line['struct_comm_type_desc'] = ''
                st_line['struct_comm_101'] = ''
                st_line['communication'] = ''
                st_line['partner_id'] = 0
                st_line['counterparty_name'] = ''
                st_line['counterparty_number'] = ''
                st_line['globalisation_level'] = False
                st_line['globalisation_amount'] = False
                st_line['amount'] = False
                      
                st_line['name'] = line[2:10]
                # positions 11-31 not processed (informational bank ref nbr) 
                st_line_amt = list2float(line[32:47])
                if line[31] == '1':    # 1=debit
                    st_line_amt = - st_line_amt
                    st_line['account_id'] = def_pay_acc
                else:
                    st_line['account_id'] = def_rec_acc
                # processing of amount depending on globalisation code    
                glob_lvl = int(line[124])
                if glob_lvl > 0: 
                    if glob_lvl_stack[-1] == glob_lvl: 
                        st_line['amount'] = st_line_amt
                        glob_lvl_stack.pop()
                    else:
                        glob_lvl_stack.append(glob_lvl)
                        st_line['type'] = 'globalisation'
                        st_line['globalisation_level'] = glob_lvl
                        st_line['globalisation_amount'] = st_line_amt
                else:
                    st_line['amount'] = st_line_amt
                # positions 48-53 : Value date or 000000 if not known (DDMMYY)
                st_line['val_date'] = str2date(line[47:53])
                # positions 54-61 : transaction code
                st_line['trans_type'] = line[53]
                trans_type_ids = trans_type_obj.search(cr , uid, [('type' ,'=', st_line['trans_type'])])
                if not trans_type_ids:
                    raise wizard.except_wizard(_('Data Error!'), 
                        _('The File contains an invalid CODA Transaction Type : %s!') % (st_line['trans_type']))
                st_line['trans_type_desc'] = trans_type_obj.browse(cr, uid, trans_type_ids[0], context).description          
                st_line['trans_family'] = line[54:56]
                trans_family_ids = trans_code_obj.search(cr , uid, 
                    [('type', '=', 'family'),('code', '=', st_line['trans_family'])])
                if not trans_family_ids:
                    raise wizard.except_wizard(_('Data Error!'), 
                        _('The File contains an invalid CODA Transaction Family : %s!') % (st_line['trans_family']))
                st_line['trans_family_desc'] = trans_code_obj.browse(cr, uid, trans_family_ids[0], context).description
                st_line['trans_code'] = line[56:58]
                trans_code_ids = trans_code_obj.search(cr , uid, 
                    [('parent_id', '=', trans_family_ids[0]),('type', '=', 'code'),('code', '=', st_line['trans_code'])])
                if trans_code_ids:
                    st_line['trans_code_desc'] = trans_code_obj.browse(cr, uid, trans_code_ids[0], context).description
                else:
                    st_line['trans_code_desc'] = _('Transaction Code unknown, please consult your bank.')
                st_line['trans_category'] = line[58:61]
                trans_category_ids = trans_category_obj.search(cr , uid, [('category' ,'=', st_line['trans_category'])])
                if trans_category_ids:
                    st_line['trans_category_desc'] = trans_category_obj.browse(cr, uid, trans_category_ids[0], context).description
                else:
                    st_line['trans_category_desc'] = _('Transaction Category unknown, please consult your bank.')              
                # positions 61-115 : communication                
                if line[61] == '1':
                    st_line['struct_comm_type'] = line[62:65]
                    comm_code_ids = comm_type_obj.search(cr , uid, [('code' ,'=', st_line['struct_comm_type'])])
                    if not comm_code_ids:
                        raise wizard.except_wizard(_('Data Error!'), 
                            _('The File contains an invalid Structured Communication Type : %s!') % (st_line['struct_comm_type']))
                    st_line['struct_comm_type_desc'] = comm_type_obj.browse(cr, uid, comm_code_ids[0], context).description
                    st_line['communication'] = line[65:115]
                    if st_line['struct_comm_type'] == '101':
                        st_line['struct_comm_101'] = line[65:77]
                else:
                    st_line['communication'] = line[62:115]
                st_line['entry_date'] = str2date(line[115:121])
                # positions 122-124 not processed

                bank_statement_lines[st_line['name']] = st_line
                bank_statement['bank_statement_lines'] = bank_statement_lines
            elif line[1] == '2':
                # movement data record 2.2
                st_line_name = line[2:10]
                bank_statement['bank_statement_lines'][st_line_name]['communication'] += line[10:63]
            elif line[1] == '3':
                # movement data record 2.3
                st_line_name = line[2:10]
                st_line_partner_acc = str(line[10:47]).strip().lower()
                counterparty_number = line[10:47]
                counterparty_name = line[47:82]
                bank_statement['bank_statement_lines'][st_line_name]['communication'] += line[82:125]
                if st_line_partner_acc:
                    bank_ids = pool.get('res.partner.bank').search(cr,uid,[('iban','=', st_line_partner_acc)])
                else:
                    bank_ids = False
                if bank_ids:
                    bank = pool.get('res.partner.bank').browse(cr, uid, bank_ids[0], context)
                    line = bank_statement_lines[st_line_name]
                    line['counterparty_number'] = counterparty_number
                    line['counterparty_name'] = counterparty_name
                    if line and bank.partner_id:
                        line['partner_id'] = bank.partner_id.id
                        if line['amount'] < 0 :
                            line['account_id'] = bank.partner_id.property_account_payable.id
                        else:
                            line['account_id'] = bank.partner_id.property_account_receivable.id
                        bank_statement_lines[st_line_name] = line
                else:
                    line = bank_statement_lines[st_line_name]
                    line['counterparty_number'] = counterparty_number
                    line['counterparty_name'] = counterparty_name
                    bank_statement_lines[st_line_name] = line

                bank_statement['bank_statement_lines'] = bank_statement_lines
            else:
                # movement data record 2.x (x <> 1,2,3)
                raise wizard.except_wizard(_('Data Error!'),
                     _('Movement data records of type 2.%s are not supported !') % (line[1]))
            
        elif line[0] == '3':
            # information data record 3
            if line[1] == '1':
                # information data record 3.1
                info_line = {}
                info_line['entry_date'] = st_line['entry_date']
                info_line['type'] = 'information'
                st_line_seq = st_line_seq + 1
                info_line['sequence'] = st_line_seq
                info_line['struct_comm_type'] = ''
                info_line['struct_comm_type_desc'] = ''
                info_line['communication'] = ''
                info_line['name'] = line[2:10]
                # positions 11-31 not processed (informational bank ref nbr) 
                # positions 32-38 : transaction code
                info_line['trans_type'] = line[31]
                trans_type_ids = trans_type_obj.search(cr , uid, [('type' ,'=', info_line['trans_type'])])
                if not trans_type_ids:
                    raise wizard.except_wizard(_('Data Error!'), 
                        _('The File contains an invalid CODA Transaction Type : %s!') % (info_line['trans_type']))
                info_line['trans_type_desc'] = trans_type_obj.browse(cr, uid, trans_type_ids[0], context).description          
                info_line['trans_family'] = line[32:34]
                trans_family_ids = trans_code_obj.search(cr , uid, 
                    [('type', '=', 'family'),('code', '=', info_line['trans_family'])])
                if not trans_family_ids:
                    raise wizard.except_wizard(_('Data Error!'), 
                        _('The File contains an invalid CODA Transaction Family : %s!') % (info_line['trans_family']))
                info_line['trans_family_desc'] = trans_code_obj.browse(cr, uid, trans_family_ids[0], context).description
                info_line['trans_code'] = line[34:36]
                trans_code_ids = trans_code_obj.search(cr , uid, 
                    [('parent_id', '=', trans_family_ids[0]),('type', '=', 'code'),('code', '=', info_line['trans_code'])])
                if trans_code_ids:
                    info_line['trans_code_desc'] = trans_code_obj.browse(cr, uid, trans_code_ids[0], context).description
                else:
                    info_line['trans_code_desc'] = _('Transaction Code unknown, please consult your bank.')
                info_line['trans_category'] = line[36:39]
                trans_category_ids = trans_category_obj.search(cr , uid, [('category' ,'=', info_line['trans_category'])])
                if trans_category_ids:
                    info_line['trans_category_desc'] = trans_category_obj.browse(cr, uid, trans_category_ids[0], context).description
                else:
                    info_line['trans_category_desc'] = _('Transaction Category unknown, please consult your bank.')              
                # positions 40-113 : communication                
                if line[39] == '1':
                    info_line['struct_comm_type'] = line[40:43]
                    comm_code_ids = comm_type_obj.search(cr , uid, [('code' ,'=', info_line['struct_comm_type'])])
                    if not comm_code_ids:
                        raise wizard.except_wizard(_('Data Error!'), 
                            _('The File contains an invalid Structured Communication Type : %s!') % (info_line['struct_comm_type']))
                    info_line['struct_comm_type_desc'] = comm_type_obj.browse(cr, uid, comm_code_ids[0], context).description
                    info_line['communication'] = line[43:113]
                else:
                    info_line['communication'] = line[40:113]
                # positions 114-128 not processed
                bank_statement_lines[info_line['name']] = info_line
                bank_statement['bank_statement_lines'] = bank_statement_lines
            elif line[1] == '2':
                # information data record 3.2
                info_line_name = line[2:10]
                bank_statement['bank_statement_lines'][info_line_name]['communication'] += line[10:115]
            elif line[1] == '3':
                # information data record 3.3
                info_line_name = line[2:10]
                bank_statement['bank_statement_lines'][info_line_name]['communication'] += line[10:100]
               
        elif line[0] == '4':
            # free communication data record 4
            comm_line = {}
            comm_line['type'] = 'communication'
            st_line_seq = st_line_seq + 1
            comm_line['sequence'] = st_line_seq
            comm_line['name'] = line[2:10]
            comm_line['communication'] = line[32:112]
            bank_statement_lines[comm_line['name']] = comm_line
            bank_statement['bank_statement_lines'] = bank_statement_lines

        elif line[0] == '8':
            # new balance record
            bal_end = list2float(line[42:57])
            if line[41] == '1':    # 1=Debit
                bal_end = - bal_end
            bank_statement['balance_end_real'] = bal_end

        elif line[0] == '9':
            # footer record
            bank_statements.append(bank_statement)
    #end for
    
    bk_st_list = []
    nb_err = 0
    err_log = _('CODA Import failed !')
    coda_id = 0
    coda_note = ''
    line_note = ''
    
    coda_id = pool.get('account.coda').search(cr, uid,[
        ('name', '=', codafilename),
        ('coda_creation_date', '=', bank_statement['date']),
        ])
    if coda_id:
        raise wizard.except_wizard(_('CODA Import failed !'),
            _("CODA file with Filename '%s' and Creation Date '%s' has already been imported !")
            % (codafilename, bank_statement['date']))    
    
    try:
        coda_id = pool.get('account.coda').create(cr, uid,{
            'name' : codafilename,
            'coda_data': codafile,
            'coda_creation_date' : bank_statement['date'],
            'date': time.strftime('%Y-%m-%d'),
            'user_id': uid,
            })

    except osv.except_osv, e:
        cr.rollback()
        nb_err += 1
        err_log = err_log +'\n\nApplication Error : ' + str(e)
    except Exception, e:
        cr.rollback()
        nb_err += 1
        err_log = err_log +'\n\nSystem Error : ' +str(e)       
    except :
        cr.rollback()
        nb_err += 1
        err_log = err_log +'\n\nUnknown Error'        
    
    for statement in bank_statements:
        try:
            
            bk_st_id = pool.get('coda.bank.statement').create(cr, uid, {
                'name': statement['coda_seq_number'],
                'journal_id': statement['journal_id'],
                'coda_id': coda_id,
                'date': statement['date'],
                'period_id': statement['period_id'],
                'balance_start': statement['balance_start'],
                'balance_end_real': statement['balance_end_real'],
                'state':'draft',
            })

            lines = statement['bank_statement_lines']
            for value in lines:
                line = lines[value]
                
                if line['type'] == 'information':
                    line_note = 'Transaction Type' ': %s - %s'                  \
                        '\nTransaction Family: %s - %s'                         \
                        '\nTransaction Code: %s - %s'                           \
                        '\nTransaction Category: %s - %s'                       \
                        '\nStructured Communication Type: %s - %s'              \
                        '\nCommunication: %s'                                   \
                        %(line['trans_type'], line['trans_type_desc'],
                          line['trans_family'], line['trans_family_desc'],
                          line['trans_code'], line['trans_code_desc'],
                          line['trans_category'], line['trans_category_desc'],
                          line['struct_comm_type'], line['struct_comm_type_desc'],
                          line['communication'])

                    id = pool.get('coda.bank.statement.line').create(cr, uid, {
                               'sequence': line['sequence'],                                                  
                               'name': line['name'],
                               'type' : 'information',               
                               'date': line['entry_date'],                
                               'statement_id': bk_st_id,
                               'note': line_note,
                               })
                        
                elif line['type'] == 'communication':
                    line_note =  'Free Communication:\n %s'                     \
                        %(line['communication'])

                    id = pool.get('coda.bank.statement.line').create(cr, uid, {
                               'sequence': line['sequence'],                                                  
                               'name': line['name'],
                               'type' : 'communication',
                               'date': statement['date'],
                               'statement_id': bk_st_id,
                               'note': line_note,
                               })

                else:
                    line_note = _('Partner name: %s \nPartner Account Number: %s' \
                        '\nTransaction Type: %s - %s'                             \
                        '\nTransaction Family: %s - %s'                           \
                        '\nTransaction Code: %s - %s'                             \
                        '\nTransaction Category: %s - %s'                         \
                        '\nStructured Communication Type: %s - %s'                \
                        '\nCommunication: %s'                                     \
                        '\nValuta Date: %s'                                       \
                        '\nEntry Date: %s \n')                                    \
                        %(line['counterparty_name'], line['counterparty_number'],
                          line['trans_type'], line['trans_type_desc'],
                          line['trans_family'], line['trans_family_desc'],
                          line['trans_code'], line['trans_code_desc'],
                          line['trans_category'], line['trans_category_desc'],
                          line['struct_comm_type'], line['struct_comm_type_desc'],
                          line['communication'],
                          line['val_date'],
                          line['entry_date'])

                    if line['type'] == 'globalisation':
                        id = pool.get('coda.bank.statement.line').create(cr, uid, {
                               'sequence': line['sequence'],                                                  
                               'name': line['name'],
                               'type' : 'globalisation',
                               'date': line['entry_date'],
                               'globalisation_level': line['globalisation_level'],  
                               'globalisation_amount': line['globalisation_amount'],                                                      
                               'partner_id': line['partner_id'] or 0,
                               'account_id': line['account_id'],
                               'statement_id': bk_st_id,
                               'note': line_note,
                               'ref': line['struct_comm_101'],
                               })
                    else:
                        id = pool.get('coda.bank.statement.line').create(cr, uid, {
                               'sequence': line['sequence'],                                                  
                               'name': line['name'],
                               'type' : 'general',
                               'date': line['entry_date'],
                               'amount': line['amount'],
                               'partner_id': line['partner_id'] or 0,
                               'account_id': line['account_id'],
                               'statement_id': bk_st_id,
                               'note': line_note,
                               'ref': line['struct_comm_101'],
                               })

            cr.commit()

            bk_st_journal = journal_obj.browse(cr, uid, statement['journal_id'], context).name
            coda_note = coda_note +                                                 \
                _('\n\nBank Journal: %s'                                            \
                '\nCODA Sequence Number: %s'                                        \
                '\nAccount Number: %s'                                              \
                '\nAccount Holder Name: %s'                                         \
                '\nDate: %s, Starting Balance:  %.2f, Ending Balance: %.2f')        \
                %(bk_st_journal,
                  statement['coda_seq_number'],
                  statement['acc_number'],
                  statement['acc_holder'],
                  statement['date'], float(statement['balance_start']), float(statement['balance_end_real']))

            bk_st_list.append(bk_st_id)

        except osv.except_osv, e:
            cr.rollback()
            nb_err += 1
            err_log = err_log + _('\n\nApplication Error : ') + str(e)
        except Exception, e:
            cr.rollback()
            nb_err += 1
            err_log = err_log + _('\n\nSystem Error : ') +str(e)          
        except :
            cr.rollback()
            nb_err += 1
            err_log = err_log + _('\n\nUnknown Error')

    coda_note_header = _('CODA File is Imported  :')
    coda_note_footer = _('\n\nNumber of statements : ') + str(len(bk_st_list))
    err_log = err_log + _('\nNumber of errors : ') + str(nb_err) + '\n'
    if not nb_err:
        pool.get('account.coda').write(cr, uid,[coda_id],{'note': coda_note_header + coda_note + coda_note_footer })
        return {'note': coda_note_header + coda_note + coda_note_footer, 
                'coda_id': coda_id,
                }
    else:
        return {'note': err_log, 
                'coda_id': coda_id,
                }

def str2date(date_str):
            return time.strftime('%Y-%m-%d', time.strptime(date_str,'%d%m%y'))

def str2float(str):
    try:
        return float(str)
    except:
        return 0.0

def list2str(lst):
            return str(lst).strip('[]').replace(',', '').replace('\'', '')

def list2float(lst):
            try:
                return str2float((lambda s : s[:-3] + '.' + s[-3:])(lst))
            except:
                return 0.0

class coda_import(wizard.interface):
    def _action_open_window(self, cr, uid, data, context):
        form = data['form']
        return {
            'domain': "[('coda_id','=',%d)]" %(form['coda_id']),
            'name': 'CODA Bank Statements',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'coda.bank.statement',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : codawiz_form,
                    'fields' : codawiz_fields,
                    'state' : [('extraction', '_Ok') ]}
        },
        'extraction' : {
            'actions' : [_coda_parsing],
            'result' : {'type' : 'form',
                    'arch' : result_form,
                    'fields' : result_fields,
                    'state' : [('end', '_Close'),('open', '_View Statement(s)')]}
        },
        'open': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state': 'end'}
            },
    }
coda_import('noviat.account.coda.import')

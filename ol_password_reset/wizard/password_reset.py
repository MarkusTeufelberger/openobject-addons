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
import wizard
import pooler
from osv import osv
from tools.translate import _

wiz_form = '''<?xml version="1.0"?>
<form string="Credential Mailer/Changer">
    <field name="user" />
    <field name="password" password="1"/>
</form>'''
wiz_fields = {
        'user': {'string':'User', 'type':'many2one','relation':'res.users','default':False, 'required':True},
        'password': {'string':'Your Password', 'type':'char','size':100,'invisible':True,'required':True},
}

def _resetPassword(self, cr, uid, data, context):
    obj = pooler.get_pool(cr.dbname).get('res.users')
    #Check current user's password
    curr_user = obj.browse(cr,uid,uid)
    if data['form']['password'] == curr_user.password:
        #Reset password    
        obj.reset_password(cr,uid,data['form']['user'])
    else:
        raise osv.except_osv(
                _('Wrong Password'),
                _("You cannot reset another users password since you entered the wrong password'."))
    return {}

def _sendPassword(self, cr, uid, data, context):
    obj = pooler.get_pool(cr.dbname).get('res.users')
    #Check current user's password
    curr_user = obj.browse(cr,uid,uid)
    if data['form']['password'] == curr_user.password:
        #Reset password    
        obj.send_password(cr,uid,data['form']['user'])
    else:
        raise osv.except_osv(
                _('Wrong Password'),
                _("You cannot reset another users password since you entered the wrong password'."))
    return {}
    
class wizard_pwreset(wizard.interface):

    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch':wiz_form, 'fields':wiz_fields, 'state':[('end', 'Cancel'), ('resetpass', 'Reset Now')]}
        },
        'resetpass': {
            'actions': [_resetPassword],
            'result': {'type':'state', 
                       'state':'end'}
        }

    }
wizard_pwreset('res.users.reset')

class wizard_pwreset(wizard.interface):

    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch':wiz_form, 'fields':wiz_fields, 'state':[('end', 'Cancel'), ('sendpass', 'Send Now')]}
        },
        'sendpass': {
            'actions': [_sendPassword],
            'result': {'type':'state', 
                       'state':'end'}
        }

    }
wizard_pwreset('res.users.send')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


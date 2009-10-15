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
import time
import wizard


dates_form = '''<?xml version="1.0"?>
<form string="select a month for commision">
    <field name="period_id"/>
</form>'''

dates_fields = {
    'period_id': {'string':'Period', 'type':'many2one', 'relation': 'account.period'},
}

class wizard_report(wizard.interface):
    states = {
        'init': {
            'actions': [], 
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancel'),('report','Print Commission.')]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'sale.agent', 'state':'end'}
        }
    }
wizard_report('sale.agent')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


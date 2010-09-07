# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Vincent Renaville
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

import wizard
import netsvc
import time
import pooler
from osv import osv

from mx import DateTime

init_form = '''<?xml version="1.0"?>
<form string="Enter the date : ALL days between those dates will be complete with holidays.">
    <field name="date_from"/>
    <field name="date_to" />
    <field name="analytic_account" domain="[('type','=','normal'),('state','&lt;&gt;','pending'),('state','&lt;&gt;','close')]"/>
    <field name="nb_hours"/>
    <field name="libelle"/>
</form>'''

init_fields = {
    'date_from': {'string':"Date from", 'type':'date','required':True},
    'date_to': {'string':"Date to", 'type':'date','required':True},
    'libelle': {'string':"Libelle", 'type':'char','size':'100','required':True},
    'analytic_account': {'string': 'Analytic account', 'type': 'many2one', 'relation':'account.analytic.account', 'required':True},
    'nb_hours': {'string':"Nb hours a day", 'type':'float','required':True},
}


def _get_number_days_between_dates(cr, uid, context,date_from,date_to):
    datetime_from=DateTime.strptime(date_from, '%Y-%m-%d')
    datetime_to=DateTime.strptime(date_to, '%Y-%m-%d')
    difference=datetime_to+1-datetime_from
    weeks, days = divmod(difference.days, 7)
    return int(difference.days)
#----------------------------- 
# # Dates produce timedeltas when subtracted.
# 
# diff = date2 - date1
# diff = datetime.date(year1, month1, day1) - datetime.date(year2, month2, day2)
# #----------------------------- 
# 
# bree = datetime.datetime(1981, 6, 16, 4, 35, 25)
# nat  = datetime.datetime(1973, 1, 18, 3, 45, 50)
# 
# difference = bree - nat
# print "There were", difference, "minutes between Nat and Bree"
# #=> There were 3071 days, 0:49:35 between Nat and Bree
# 
# weeks, days = divmod(difference.days, 7)
# 
# minutes, seconds = divmod(difference.seconds, 60)
# hours, minutes = divmod(minutes, 60)
# 
# print "%d weeks, %d days, %d:%d:%d" % (weeks, days, hours, minutes, seconds)
# #=> 438 weeks, 5 days, 0:49:35
# 
# #----------------------------- 
# print "There were", difference.days, "days between Bree and Nat." 
# #=> There were 3071 days between bree and nat

def _altern_si_so(cr, uid, context,ids):
    for id in ids:
        sql = '''
        select action, name
        from hr_attendance as att
        where employee_id = (select employee_id from hr_attendance where id=%s)
        and action in ('sign_in','sign_out')
        and name <= (select name from hr_attendance where id=%s)
        order by name desc
        limit 2
        ''' % (id, id)
        cr.execute(sql)
        atts = cr.fetchall()
        if not ((len(atts)==1 and atts[0][0] == 'sign_in') or (atts[0][0] != atts[1][0] and atts[0][1] != atts[1][1])):
            return False
    return True

# Return employee Name & id + compute time for today
def _complete(self, cr, uid, data, context):
    form = data['form']
    #ts = data['ids']
    pool = pooler.get_pool(cr.dbname)
    user_ids = pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)])
    if not len(user_ids):
        raise wizard.except_wizard('Error !', 'No employee defined for your user !')

    # Get the current timesheet
    ts = pool.get('hr_timesheet_sheet.sheet')
    timesheets = ts.browse(cr, uid, data['ids'])
    
    # nb_hours not > 24h
    if form['nb_hours'] > 24 or form['nb_hours'] < 1:
        raise wizard.except_wizard('Only 24 hours a day max, 1 hour min', 'Please, set another value for nb hours a day.')
    # compute hours in datetime format
    hh_mm = divmod(form['nb_hours']*60,60)
    

    #Get the analytic account
    # a_a_ids = pool.get('account.analytic.account').search(cr, uid, form['analytic_account'])
    a_a=pool.get('account.analytic.account').browse(cr, uid, form['analytic_account'], context)

    for timesheet in  timesheets:
        # Verify state, they all  must be draft  raise error if already confirmed
        if timesheet.state <>'draft':
            raise wizard.except_wizard('Error !', 'You can not modify a confirmed timesheet, please ask the manager !')
        # Verify the date must be in ts dates
        if timesheet.date_from > form['date_from']:
            raise wizard.except_wizard('Error !', 'Your date_from must be in timesheet dates !')
        if timesheet.date_to < form['date_to']:
            raise wizard.except_wizard('Error !', 'Your date_to must be in timesheet dates !')
        
        #Pour chaque jour contenu de date_from a date_to
        
        for day in range(_get_number_days_between_dates(cr, uid, context, form['date_from'], form['date_to'])):
            datetime_current=(DateTime.strptime(form['date_from'], '%Y-%m-%d') + DateTime.RelativeDateTime(days=day)).strftime('%Y-%m-%d')
            # Create the analytic line
            ligne_analytic_to_create =  pool.get('hr.analytic.timesheet')
            unit_id = ligne_analytic_to_create._getEmployeeUnit(cr, uid, context)
            product_id = ligne_analytic_to_create._getEmployeeProduct(cr, uid, context)
            res={}
            res = {
                'name': form['libelle'] or 'Holidays',
                'date': datetime_current,
                'unit_amount': form['nb_hours'],
                'product_uom_id': unit_id,
                'product_id': product_id,
                'amount': form['nb_hours'],
                'account_id': a_a.id,
                'to_invoice':a_a.to_invoice.id,
                'sheet_id':timesheet.id,
            }
            res2 = ligne_analytic_to_create.on_change_unit_amount(cr, uid, False, product_id, form['nb_hours'],unit_id, context)
            if res2:
                res.update(res2['value'])
            
            id = ligne_analytic_to_create.create(cr, uid, res, context)
            # If there is no other attendances, create it
            # create the attendances:
            ligne_att =  pool.get('hr.attendance')
            if len(ligne_att.search(cr, uid, [('name','=',datetime_current),('employee_id','=',user_ids[0])]))<1:
                date_to_write_to = datetime_current+" 00:00:00"
                res = {
                    'name': DateTime.strptime(date_to_write_to,'%Y-%m-%d %H:%M:%S'),
                    'action' : 'sign_in',
                    'employee_id' : user_ids[0],
                    'sheet_id':timesheet.id,
                }
                date_end=" %d:%d:00"%(hh_mm[0],hh_mm[1])
                res2 = {
                    'name': DateTime.strptime(datetime_current+date_end,'%Y-%m-%d %H:%M:%S'),
                    'action' : 'sign_out',
                    'employee_id' : user_ids[0],
                    'sheet_id':timesheet.id,
                }
                id = ligne_att.create(cr, uid, res, context)
                id = ligne_att.create(cr, uid, res2, context)
    return {}

class wizard_report(wizard.interface):
    states = {
        'init': {
            'actions': [], 
            'result': {'type':'form', 'arch':init_form, 'fields':init_fields, 'state':[ ('end','Exit','gtk-cancel'),('complete','complete','gtk-ok')]}
        },
        'complete': {
            'actions': [_complete],
            'result': {'type':'state', 'state':'end'}
        }
    }
wizard_report('hr.holiday.fullfill.timesheetc2c')



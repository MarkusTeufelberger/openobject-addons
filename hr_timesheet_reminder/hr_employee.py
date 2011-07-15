# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Arnaud Wüst (Camptocamp)
# Author : Guewen Baconnier (Camptocamp)
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
import time

from osv import fields, osv


class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _columns = {
            'receive_timesheet_alerts': fields.boolean('Receive Timesheet Alerts'),
    }

    _defaults = {
            'receive_timesheet_alerts': lambda *a: True,
    }

    def compute_timesheet_status(self, cr, uid, ids, period, context):
        """ return the timesheet status for an employee
         from its id and a period (tuple from date-to date)"""
        status = 'Error'

        if isinstance(ids, list):
            ids = ids[0]

        employee = self.browse(cr, uid, ids, context=context)

        time_from = time.strptime(str(period[0]), "%Y-%m-%d %H:%M:%S.00")
        time_to = time.strptime(str(period[1]), "%Y-%m-%d %H:%M:%S.00")
        
        # does the timesheet exsists in db and what is its status?
        timeformat = "%Y-%m-%d"
        date_from = time.strftime(timeformat, time_from)
        date_to = time.strftime(timeformat, time_to)

        cr.execute("""SELECT state, date_from, date_to
                   FROM hr_timesheet_sheet_sheet
                   WHERE employee_id = %s
                   AND date_from >= %s
                   AND date_to <= %s""",
            (employee.id, date_from, date_to))
        sheets = cr.dictfetchall()

        #the timesheet does not exists in db
        if not sheets:
            status = 'Missing'

        if len(sheets) > 0:
            status = 'Confirmed'
            for s in sheets:
                if s['state'] == 'draft':
                    status = 'Draft'
        return status

hr_employee()

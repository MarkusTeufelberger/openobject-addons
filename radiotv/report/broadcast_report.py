# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

import pooler
import time
from report import report_sxw
import common

class broadcast_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(broadcast_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'obt_date': self.obt_date,
            'obt_time': self.obt_time,
            'lang': context['lang'],
        })

    def obt_date(self, date, items=3, sep='-'):
        return common.obt_date(self, date, items, sep)

    def obt_time(self, date, items=3, sep=':'):
        return common.obt_time(self, date, items, sep)


report_sxw.report_sxw('report.radiotv.broadcast.report', 'radiotv.broadcast',
        'addons/radiotv/report/broadcast_report.rml',
        parser=broadcast_report, header=False)

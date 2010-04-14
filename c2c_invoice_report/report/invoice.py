##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
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
from mx.DateTime import *
from report import report_sxw
import xml
import pdb
import tools
import pooler


class Account_invoice_stdc2c(report_sxw.rml_parse):
    _name = 'report.account.invoice_c2c'

        
    def get_trans(self, lang, source, name):
        ids = self.pool.get('ir.translation').search(
                                                        self.cr, 
                                                        self.uid, 
                                                        [
                                                            ['name','=',name], 
                                                            ['lang','=',lang], 
                                                            ['src','=', source]
                                                        ]
                                                    )
        
        if not ids :
            return source
        else :
            if not isinstance(ids, list) :
                ids = [ids]
            return self.pool.get('ir.translation').browse(self.cr, self.uid, ids[0]).value
            
   
        
    def __init__(self, cr, uid, name, context=None):
        super(Account_invoice_stdc2c, self).__init__( cr, uid, name, context)
        self.grant = {}
        
        self.pool = pooler.get_pool(self.cr.dbname)
        self.localcontext.update({
            'time': time,
            'get_trans':self.get_trans,
        })
        




report_sxw.report_sxw(
                        'report.account.invoice_c2c',
                        'account.invoice',
                        'addons/c2c_invoice_report/report/invoice.rml',
                        parser=Account_invoice_stdc2c
                    )

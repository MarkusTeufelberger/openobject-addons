# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2009 Àngel Àlvarez - NaN  (http://www.nan-tic.com) All Rights Reserved.
#
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

import datetime

from osv import fields,osv

class pricelist_partnerinfo(osv.osv):
    _name = 'pricelist.partnerinfo'
    _inherit = 'pricelist.partnerinfo'

    def _valid(self, cr, uid, ids, field_name, args, context=None):
        result = {}
        today = datetime.date.today()
        today = today.strftime('%Y-%m-%d')
        for info in self.browse(cr, uid, ids, context):
            if info.state in ['buy','quotation'] and ( not info.date_start or today >= info.date_start ) and ( not info.date_end or today <= info.date_end ):
                result[info.id] = True
            else:
                result[info.id] = False
        return result

    _columns = {
        'state':fields.selection( [ ('buy','Buy'),('quotation','Quotation'),('waiting','Waiting'),('no-work','Not Worked')] , 'State' ),
        'date_start': fields.date('Start Date', help="Starting date for this pricelist version to be valid."),
        'date_end': fields.date('End Date', help="Ending date for this pricelist version to be valid."),
        'valid': fields.function(_valid, method=True, type='boolean', string='Valid', store=False, help='Indicates if the line is valid in the current date. A line will only be valid if today is between Start and End dates and the line is in Buy state.'),
        'price': fields.float('Unit Price', required=True, digits=(16,4)),
    }

pricelist_partnerinfo()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

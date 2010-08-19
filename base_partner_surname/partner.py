# -*- coding: utf-8 -*-
##############################################################################
#
#    base_partner_surname module for OpenERP, add firstname and lastname in partner
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
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
from osv import fields,osv

class res_partner_address(osv.osv):
    _inherit ='res.partner.address'

    def _get_name_calc(self, cr, uid, ids, field_name, unknow_none, context):
        """
        This is for overriding object 'name' property 
        """
        ar_ctc = self.read(cr,uid,ids, ['id', 'first_name', 'last_name'], context)
        res={}
        for record in ar_ctc:
            _name = "%s %s" % (record['first_name'] or '', record['last_name'] or '')
            res[record['id']] = _name
        return res


    _columns = {
        'first_name': fields.char('First Name', size=63),
        'last_name': fields.char('Last Name', size=64),
        'name': fields.function(_get_name_calc, type='char', size=128, method=True, string='Name'),
    }


    def _name_get(self, cr, uid, ids, context=None):
        """
        This is for overriding relation use
        """
        if not context: context={}
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['first_name', 'last_name'], context)
        res = []
        for record in reads:
            _name = "%s %s" % (record['first_name'] or '', record['last_name'] or '')
            res.append((record['id'], _name))
        return res


    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        return self._name_get(cr, uid, ids, context)

res_partner_address()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


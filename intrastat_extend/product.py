# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

from osv import osv
from tools.translate import _

class product_template(osv.osv):
    """add an on_change to manages the intrastat selection"""
    _inherit = "product.template"

    def onchange_intrastat_id(self, cr, uid, ids, intrastat=False, context= None):
        """if select an intrastat reg without code it not allow select it"""
        if intrastat:
            intrastat_obj = self.pool.get('report.intrastat.code').browse(cr, uid, intrastat)
            if not intrastat_obj.name:
                return {'value': {'intrastat_id': None}, 'warning': {'title': _('Warning'), 'message': _('Cannot select an intrastat without code') }}
        return {}

product_template()

class product_product(osv.osv):
    """add an on_change to manages the intrastat selection"""
    _inherit = "product.product"

    def onchange_intrastat_id(self, cr, uid, ids, intrastat=False, context= None):
        """if select an intrastat reg without code it not allow select it"""
        if intrastat:
            intrastat_obj = self.pool.get('report.intrastat.code').browse(cr, uid, intrastat)
            if not intrastat_obj.name:
                return {'value': {'intrastat_id': None}, 'warning': {'title': _('Warning'), 'message': _('Cannot select an intrastat without code') }}
        return {}

product_product()
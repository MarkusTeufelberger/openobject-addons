# -*- coding: utf-8 -*-
##############################################################################
#
#    sale_retails module for OpenERP, allows the management of deposit
#
#    Copyright (C) 2009 Akretion.com. All Rights Reserved
#    authors: Raphaël Valyi
#
#    Copyright (C) 2010 SYLEAM Info Services (<http://www.syleam.fr/>) Suzanne Jean-Sebastien
#
#    This file is a part of sale_retails
#
#    sale_retails is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    sale_retails is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
                'pos_enabled': fields.boolean('POS Enabled'),
                }
    
    _defaults = {
                 'pos_enabled': lambda * a:True,
                 }
account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

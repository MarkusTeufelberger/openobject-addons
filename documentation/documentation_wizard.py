# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved
#                       http://www.NaN-tic.com
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
from osv import fields
from tools.translate import _


class documentation_import_wizard(osv.osv_memory):
    _name='documentation.import.wizard'

    _columns = {
    }

    def action_import(self, cr, uid, ids, context=None):
        self.pool.get('ir.documentation.paragraph')._import_documentation(cr, uid, context)
        return {}

    def action_cancel(self, cr, uid, ids, context=None):
        return {}

documentation_import_wizard()

class documentation_build_wizard(osv.osv_memory):
    _name='documentation.build.wizard'

    _columns = {
    }

    def action_build(self, cr, uid, ids, context=None):
        self.pool.get('ir.documentation.paragraph').export_to_html(cr, uid, context)
        return {}

    def action_cancel(self, cr, uid, ids, context=None):
        return {}

documentation_build_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

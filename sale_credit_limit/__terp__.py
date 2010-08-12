# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai <gdukai@gmail.com>
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
{
    'name': 'Sale Order Credit Limit for Partners',
    'version': '1.0',
    "author" : "Gábor Dukai",
    "website" : "http://exploringopenerp.blogspot.com",
    "license" : "GPL-3",
    "description": """
    The Sale Order confirming button checks if the partner's
    receivables minus payables plus the order's total
    exceeds her credit limit.
    If it does, it doesn't let the user to confirm the order.
    Managers have an extra button to bypass the check but
    of course the credit limit itself could be lifted, too.
    """,
    'depends': ["sale"],
    'init_xml': [],
    'update_xml': [
        'sale_workflow.xml',
        'sale_view.xml',
    ],
    'installable': True,
    'active': False,
}

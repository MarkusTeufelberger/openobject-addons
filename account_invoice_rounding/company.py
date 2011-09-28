# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
##############################################################################

from osv import fields, osv


class ResCompany(osv.osv):
    """Override company to add default income account."""

    _inherit = "res.company"
    _columns = {
        'rounding': fields.integer('Rounding in cent', required=True, help='100 will round to unit never use 0'),
        'rounding_policy': fields.selection([
                ('even', 'Even'),
                ('up', 'UP'),
                ('down', 'Down'),
            ],
            'Rounding policy',
            readonly=False
            ),
        'rounding_account': fields.many2one('account.account', 'Rounding account', required=True),
        'rounding_name': fields.char('Rounding Label', required=True, translate=True, size=64),
        'rounding_in_line': fields.boolean('Rounding in invoice line not in tax', required=False, size=64),
    }
    _defaults = {
        'rounding': lambda *x: 5,
        'rounding_policy': lambda *x: 'even',
        'rounding_in_line': lambda *x: 1,
    }

ResCompany()

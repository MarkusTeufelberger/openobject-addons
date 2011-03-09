# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
#
##############################################################################
{
    'name' : 'account_invoice_rounding',
    'version' : '0.2',
    'depends' : [
                 'base',
                 'account',
                 ],
    'author' : 'Camptocamp',
    'description': """This module allows to manage custom rouding policy in customer invoices.
    It will add tax line on the invoice to match the given rouding. Configuration is done in company. You can choose rounding policy
    and it manage price accruacy paramters, you can have rounding in invoice line or tax lines""",
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [
                   'company_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
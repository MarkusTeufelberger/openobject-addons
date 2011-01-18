#-*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
##############################################################################

{
    'name': 'C2C Sale Bom split',
    'version': '1.0',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """
     This module split the product into the related packing according to their BoM when validating a sale order.
     BoM Example structure:
     
     Product A (fantom)
        Product B (normal)
            Product B1 (normal)
            Product B2 (normal)
        Product C (fantom)
            Product C1 (normal)
            Product C2 (normal)
            
     With this module, sale order of Product A will result in a packing of :

     Product B
     Product C1
     Product C2
     
     Without it will result in a packing of :
     
     Product A
     
    """,
    'author': 'Camptocamp SA',
    'website': 'http://www.camptocamp.com',
    'depends': ['sale','mrp'],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
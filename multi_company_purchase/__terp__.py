# -*- encoding: utf-8 -*-

{
    "name" : "MultiCompany Purchase Order",
    "version" : "1.1",
    "depends" : [
                  'base',
                  'purchase',
                ],
    "author" : "Axelor",
    "description": """The Module allows to define company wise Purchase Order""",
    
    'website': 'http://www.axelor.com',
    'init_xml': [],
    'update_xml': [
                
        'purchase_view.xml',

    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

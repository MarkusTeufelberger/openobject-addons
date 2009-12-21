# -*- encoding: utf-8 -*-

{
    "name" : "Homecine CRM",
    "version" : "0.1",
    "author" : "Smile.fr",
    "description": """Homecine CRM
    """,
    'website': 'http://www.smile.fr',
    'depends': ["stock", "crm", "crm_configuration"],
    'init_xml': [],
    'update_xml': ['stock_data.xml', 'crm_view.xml', 'crm_sequence.xml', 'stock_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

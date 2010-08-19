#
#  company.py
#
#  Created by Nicolas Bessi
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
#
from osv import osv, fields

class ResCompany(osv.osv):
    """override the company in order to add ldap config param"""
    _inherit = 'res.company'
    _columns = {
        ## the main user ldad branch without the OU
        'api_id' :  fields.char('Yubico ID', size=128, help="This is the Yubico API id provided by yubico.com"),     
        ## the API key
        'api_key' :  fields.char('Yubico API Key', size=256, help = 'not implemented yet we trust ssl'),
                    }
ResCompany()
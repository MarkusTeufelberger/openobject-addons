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
        'otp_active' :  fields.boolean('OTP active'),     
    }
ResCompany()
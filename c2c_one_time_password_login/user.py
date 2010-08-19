#
#  user.py
#
#  Created by Nicolas Bessi
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
#
from osv import osv, fields

class ResUSers(osv.osv):
    """override the company in order to add ldap config param"""
    ## login session
    _loginsession = {}
    ##OTP time to live
    _otp_ttl = 300 #sec
    _inherit = 'res.users'
    _columns = {
        ##otp sercet key of user
        'otp_key' :  fields.char(
                                        'OTP key', 
                                        size=128, 
                                        help="This is the otp key system identifier"
                                    ),      
 }
ResUSers()
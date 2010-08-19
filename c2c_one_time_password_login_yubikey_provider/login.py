#
#  login.py
#
#  Created by Nicolas Bessi
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
#
from service import security
from osv import fields,osv
import netsvc
import pooler
import tools
import datetime
import c2c_one_time_password_login
import urllib2
import re
## Code taken from google http://code.google.com/p/yubico-python-client/
##






#Function to override
def check_otp(otp, user, res_user_obj):
    """Validate OTP"""
    def verify(clientId,otp, user):
        YubicoAuthSrvURLprefix = 'https://api.yubico.com/wsapi/verify?id='
        AuthSrvRespRegex = re.compile('^status=(?P<rc>\w{2})')
        YubicoAuthSrvURL = YubicoAuthSrvURLprefix + clientId + "&otp=" + otp
        fh = urllib2.urlopen(YubicoAuthSrvURL)   # URL response assigned to a file handle/object

        for line in fh:
            if line == "status=OK\r\n":
                return True
        'One Time Password is invalid for user %s with otp %s'%(user.login, otp)
        return False
    #end of verifiy
    if user.otp_key != otp[0:12] :
        print 'No user for this yubikey'
        return False
    if not verify(user.company_id.api_id, otp, user) :
        return False
    res_user_obj._loginsession[user.id][otp] = datetime.datetime.now()
    return user.id

c2c_one_time_password_login.login.check_otp = check_otp
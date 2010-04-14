#
#  __terp__.py
#
#  Created by Nicolas Bessi 
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
#
{
    "name" : "c2c_one_time_password_login_yubikey_provider",
    "version" : "1.0",
    "description":""" Yubico OTP login module is a module that provide basic 
    session and mechanism for Yubico OTP product. It is based on the 
    c2c_one_time_password_login that provides generic OTP behavior.
    OTP main configuration is done on the company view. Please see the help defined in the form .
    You can find a modified version of the client on :
    lp:~c2c/openobject-client/5.0-c2c-otp
        """,
    "category" : "security",

    "depends" : [
                    "base",
                    "c2c_one_time_password_login" 
                ],
    "author" : "Camptocamp SA",
    "init_xml" : [],
    "update_xml" : [
                        "company_view.xml"
                    ],
    "installable" : True,
    "active" : False,
}
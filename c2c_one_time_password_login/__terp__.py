#
#  __terp__.py
#
#  Created by Nicolas Bessi 
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
#
{
    "name" : "c2c_one_time_password_login",
    "version" : "1.0",
    "description":""" Generic OTP login module that provides basic 
    session and mechanism for OTP.
    
    We do not intend to provide a generic framework for authentication but just one for OTP.   
    Actually it is not design to support CAS, Kerberos etc.

    The c2c_one_time_password_login provides the base mechanism for OTP 
    like authentication function overriding, user session, login management, timeout management, mutli connection, etc.
    You have one function to override in a provider module. The function is check_otp.
    A provider module let you to write a provider for a specific OTP system 
    You have a sample in the c2c_one_time_password_login_yubikey_provider module.
    The OTP configuration is done on the company view. Please see the help in the form. 
    
        """,
    "category" : "security",

    "depends" : [
                    "base", 
                ],
    "author" : "Camptocamp SA",
    "init_xml" : [],
    "update_xml" : [
                        "user_view.xml",
                        "company_view.xml"
                    ],
    "installable" : True,
    "active" : False,
}
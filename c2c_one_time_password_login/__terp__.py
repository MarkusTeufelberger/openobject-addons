#
#  __terp__.py
#
#  Created by Nicolas Bessi 
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
#
{
    "name" : "c2c_one_time_password_login",
    "version" : "1.0",
    "description":""" Generic OTP login module that provide basic 
    session and mechanisme for OTP
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
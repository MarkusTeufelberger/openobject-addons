#########################################################################
#   #####     #   #        # ####  ###     ###  #   #   ##  ###   #     #
#   #   #   #  #   #      #  #     #  #    #    # # #  #  #  #    #     #
#   ####    #   #   #    #   ###   ###     ###  #   #  #  #  #    #     #
#   #        # #    # # #    #     # #     #    #   #  ####  #    #     #
#   #         #     #  #     ####  #  #    ###  #   #  #  # ###   ####  #
# Copyright (C) 2009  Sharoon Thomas, openlabs business solutions       #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    "name" : "Password Reset & Credential sender",
    "version" : "0.1 ",
    "author" : "Sharoon Thomas, Openlabs",
    "website" : "http://launchpad.net/poweremail",
    "category" : "Added functionality - Extension",
    "depends" : ['base','poweremail'],
    "description": """
    This module uses poweremail to reset and/or send the password to a system user
    
    A new wizard 'Reset Password' and 'Send Credentials' will appear in the Administration menu
    
    How to use?
      Step 1: This module is dependent on Poweremail and will install poweremail if available.
      Step 2: Create a new Power email company account from which password mails are to be sent(minimum SMTP) and approve it. 
              (Note: Ensure that the security groups are only admins or all users will see the password mail)
      Step 3: Edit the Email templates created by this module from Poweremail > Email Templates
              and Enforce the account in the advanced tab.
      Now you can start using the 'Reset Password' and 'Send Password' Wizards in Administration.
      The screens will ask for the user whose password is to be reset and current user's password
    """,
    "init_xml": [],
    "update_xml": [
        'ol_wizard.xml',
        'template_data.xml'
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

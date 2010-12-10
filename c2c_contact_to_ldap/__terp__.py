# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp), Thanks to Laurent Lauden for his code adaptation
# Active directory Donor: M. Benadiba (Informatique Assistances.fr)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    "name" : "Camptocamp Partner extension to synchronize OpenERP with LDAP",
    "version" : "1.2",
    "author" : "Camptocamp",
    "depends" : ["base","c2c_partner_address"],
    "category" : "Generic Modules/Misc",
    "website": "http://www.camptocamp.com",
    "description": """
    
!!!!!TO BE REFACTORED!!!!!!
Live partner address synchronization through a LDAP module (inetOrgPerson). 
Tiny becomes the master of the LDAP. Each time an addresse is deleted, created or updated the same is done in the ldap (a new record is pushed).
The LDAP configuration is done in the company view. There can be one different LDAP per company! Do not forget to activate
the LDAP link in the configuration. 
The used LDAP depends on the current user company.
    
This module does not allows bulk batching synchronisation into the LDAP and is thus not suitable for an instant use with an existing LDAP.
n order to use it with an existing LDAP you have to alter the uid of contact in your LDAP. The uid should be terp_ plus the OpenERP contact id (for example terp_10).  
    
N.B: the modue requires the python-ldap library

---------------------------------------------------------------------------------------------------------------------------------------
Ce module interface les partenaires OpenERP avec un repository LDAP existant. Ainsi, OpenERP devient le master, l'interface unique
de saisie des partenaires de l'entreprise. Tous ce qui est renseigné dans OpenERP est automatiquement reporté dans 
LDAP (ajout, suppression, modification). 

L'avantage d'utiliser un tel système est la constitution d'une base de données
client unique , qui pourra s'interfacer avec un client mail (Outlook, Thunderbird, etc..) pour avoir la complétion des adresses dans la 
rédaction des mails. De plus, de nombreux systèmes de téléphonie utilisent maintenant une telle base pour la gestion des appels 
(click to dial ou remontée de fiche).


--V5 change log 
added OU specification
Unicode support --> Has python ldap does not support unicode we try to decode sting if it fail we transliterate values
Active Directory Support for Windows server 2003, Try 20008 at your own risk

""",
    "init_xml" : [
                    "security/security.xml"
                 ],
    "update_xml":[
                    'company_view.xml',
                    "wizard.xml"
                 ],
    "demo_xml" : [],
    "active": False,
    "installable": True
}

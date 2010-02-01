from osv import osv, fields

class Res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'base_dn' :  fields.char(
                                    'User dn', 
                                    size=128, 
                                    help="Exemple: cn=contacts_admin,dc=ldap,dc=dcc2c"
                                ),
        'contact_dn' : fields.char(
                                    'Bind dn', 
                                    size=128,
                                    help="Exemple: dc=ldap,dc=dcc2c -- watchout"+\
                                    " the OU will be automatically included inside"
                                ),
        'ounit' : fields.char(
                                'Contact Organizational unit of the contacts', 
                                size=128,
                                help="Exemple: Contacts"
                            ),
        'ldap_server' : fields.char(
                                        'Server address', 
                                        size=128,
                                        help="Exemple: ldap.camptocamp.com"
                                    ),
        'passwd' : fields.char('ldap password', size=128,help="Exemple: Mypassword1234"),
        'ldap_active' : fields.boolean(
                                        'Activate ldap link for this company',
                                        help='If not check nothing will be reported into the ldap'
                                        ),
        'is_activedir' : fields.boolean(
                                        'Active Directory ?', 
                                        help='The ldap is part of an Active Directory'
                                        ),
        'ldap_port' : fields.integer('ldap port (default 389)')
    }


Res_company()
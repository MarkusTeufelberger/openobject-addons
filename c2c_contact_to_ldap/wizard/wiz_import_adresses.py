# -*- encoding: utf-8 -*-

#!/usr/bin/env python2.5
#
#  init_import.py
#  Aesa
#
#  Created by Nicolas Bessi on 28.04.09.
#  Copyright (c) 2009 CamptoCamp. All rights reserved.
#

import wizard
import pooler 
import base64
import codecs
import unicodedata
import netsvc
import re
_FORM = '''<?xml version="1.0"?>
<form string="Export adresses to ldap">
</form>''' 


_FORM1 = """<?xml version="1.0"?>
<form string="Export log">
<separator colspan="4" string="Clic on 'Save as' to save the log file :" />
    <field name="errors"/>
</form>
"""

_FIELDS = {
    'errors': {
        'string': 'Error report',
        'type': 'binary',
        'readonly': True,
    },
}

### As this is a bulck batch wizzard the performance process was not reallay taken in account ###
##The ideal way of doing would be to modify the  connexion settings in order to have a connexion singelton
## in the file partner.py it will avoid connexion renegotiation for each partner.
def _action_import_adresses(self, cr, uid, data, context):
    """ This function create or update each adresses present in the database.
    It will also genreate an error report"""
    logger = netsvc.Logger()
    error_report = [u'Error report']
    add_obj = pooler.get_pool(cr.dbname).get('res.partner.address')
    add_ids = add_obj.search(cr,uid,[])
    addresses = add_obj.browse(cr, uid, add_ids)
    phone_fields = ['phone','fax','mobile','private_phone']
    for add in addresses :
        vals = {}
        vals['partner_id'] = add.partner_id.id
        vals['email'] = add.email
        vals['phone'] = add.phone
        vals['fax'] = add.fax
        vals['mobile'] = add.mobile
        vals['firstname'] = add.firstname
        vals['lastname'] = add.lastname
        vals['private_phone'] = add.private_phone
        vals['street'] = add.street
        vals['street2'] = add.street2
        vals['city'] = add.city
        #validating the datas
        if add.email :
            if re.match(
                    "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", add.email) == None or \
                re.search(u"[éèàêöüäï&]", add.email) != None:
                msg=u'Addresse %s for partner  %s has email that is invalid %s'%(
                    unicode(vals['firstname']) +' '+ unicode(vals['lastname']),
                    add.partner_id.name, 
                    unicode(add.email)
                    )
                logger.notifyChannel('ldap export', netsvc.LOG_INFO, msg)
                error_report.append(msg)
                vals['email'] = False
        for key in phone_fields :
            if not unicode(vals[key]).startswith('+')  or unicode(vals[key]).find("\n") != -1\
            or re.search(u"[éèàêöüä#&]", unicode(vals[key])) != None:
                vals[key] = False
                msg = u'Addresse %s for partner  %s has %s that is invalid '%(
                    unicode(vals['firstname']) +' '+ unicode(vals['lastname']),
                    add.partner_id.name, 
                    key
                    )
                logger.notifyChannel('ldap export', netsvc.LOG_INFO, msg)
                error_report.append(msg)
        #print add.lastname
        if not add.lastname :
            #print 'no lastname'
            vals['lastname'] = add.partner_id.name
            msg = u'!!! Addresse %s for partner  %s has no last name and first name that is valid  company name was used !!!'%(
                unicode(add.id),
                add.partner_id.name, 
                )
            logger.notifyChannel('ldap export', netsvc.LOG_INFO, msg)
            error_report.append(msg)
        add.write(vals, {'init_mode':True})
    #print error_report
    #we by pass the encoding errors
    map(lambda x: unicodedata.normalize("NFKD",x).encode('ascii','ignore'), error_report)
    error_report = "\n".join(error_report)
    print error_report
    try:
        data= base64.encodestring(error_report.encode())
    except Exception, e:
        data= base64.encodestring("Could not generate report file. Please look in the log for details") 
    
    return {'errors': data}

class Wiz_import_addresses(wizard.interface):
    states = {
        'init': {
            'actions': [],
            'result': {
                        'type': 'form', 
                        'arch':_FORM, 
                        'fields':{}, 
                        'state':[
                                    ('end','Cancel'),
                                    ('importadd','Export adresses into company LDAP')
                                ]
                        }
        },
        'importadd': {
            'actions': [_action_import_adresses],
            'result': {
                        'state':[('end', 'OK', 'gtk-ok', True)],
                        'arch' : _FORM1,
                        'fields' : _FIELDS,
                        'type':'form'
                    }
        }
    }
Wiz_import_addresses('ldap.import_adresses')

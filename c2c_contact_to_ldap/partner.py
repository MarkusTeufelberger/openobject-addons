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

from osv import osv, fields
import re
import time
import codecs
import unicodedata
try:
    import ldap
    import ldap.modlist
except :
    print 'python ldap not installed please install it in order to use this module'
import sys 

class LdapConnMApper(object):
    """LdapConnMApper: push specific fields from the Terp Partner_contacts to the
        LDAP schema inetOrgPerson. Ldap bind options are stored in company.r"""
    def __init__(self, cr, uid, osv, context=None):
        self.USER_DN = ''
        self.CONTACT_DN = ''
        self.LDAP_SERVER = ''
        self.PASS = ''
        self.OU = ''
        self.connexion = ''
        self.ACTIVDIR = False
    
        "Initialize connexion to ldap by using parameter set in the current user compagny"
        #getting ldap pref
        user = osv.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = osv.pool.get('res.company').browse(
                                                        cr, 
                                                        uid,
                                                        user.company_id.id, 
                                                        context=context
                                                    )
        self.USER_DN = company.base_dn
        self.CONTACT_DN = company.contact_dn
        self.LDAP_SERVER = company.ldap_server
        self.PASS = company.passwd
        self.PORT = company.ldap_port
        self.OU = company.ounit
        self.ACTIVDIR = company.is_activedir
        
        if self.USER_DN == '' or self.CONTACT_DN == '' or \
            self.LDAP_SERVER == '' or self.PASS == '' or self.OU == '' :
            raise Exception('Warning !', 'An LDAP parameter is missing for company %'%(company.name))
    
    def get_connexion(self):
        "create a new ldap connexion"
        print 'connecting to server ldap '+ self.LDAP_SERVER
        try:
            if self.PORT :
                self.connexion = ldap.open(self.LDAP_SERVER, self.PORT)
            else :
                self.connexion = ldap.open(self.LDAP_SERVER, 389)
            self.connexion.simple_bind_s(self.USER_DN,self.PASS)
        except Exception, e:
            raise e
        return self.connexion
        
class Contact_to_ldap_addressLdap(osv.osv):
    "Overide the CRUD of the objet in order to dnyamically bound to ldap"
    name = "contact_to_ldap.addressLdap"
    _inherit = 'res.partner.address'
    ldapMapper = None
        
    def create(self, cr, uid, vals, context={}):
        self.getconn(cr, uid, {})
        
        ids = None
        self.validate_entries(vals,cr,uid,ids)

        tmp_id = super(Contact_to_ldap_addressLdap, self).create(
                                                                cr, 
                                                                uid, 
                                                                vals, 
                                                                context
                                                                )
        if self.ldaplinkactive(cr,uid,context):
            self.saveLdapContact(tmp_id,vals,cr,uid,context)
        return tmp_id
    
    def write(self, cr, uid, ids, vals, context={}) :
        self.getconn(cr, uid, {})
        if isinstance(ids, (int, long)):
            ids = [ids]
        self.validate_entries(vals,cr,uid,ids)
        if context.has_key('init_mode') and context['init_mode'] :
            succes = True
        else :
            succes = super(Contact_to_ldap_addressLdap, self).write(
                                                                    cr, 
                                                                    uid, 
                                                                    ids, 
                                                                    vals, 
                                                                    context
                                                                    )
        if self.ldaplinkactive(cr,uid,context):
            for id in ids:
                self.updateLdapContact(id,vals,cr,uid,context)
        return succes

    def unlink(self, cr, uid, ids,context={}):
        self.getconn(cr, uid, {})
        if isinstance(ids, (int, long)):
            ids = [ids]
        if self.ldaplinkactive(cr,uid,context):
            for id in ids:
                self.removeLdapContact(id,cr,uid)
        return super(Contact_to_ldap_addressLdap, self).unlink(cr, uid, ids)
    
    def validate_entries(self,vals,cr,uid,ids):
        "Validate data of an adresses based on the inetOrgPerson shema"
        for val in vals :
            try :
                if isinstance(vals[val], basestring):
                    vals[val] = vals[val].encode('utf-8')
            except UnicodeError:
                pass
        if ids != None:
            if isinstance(ids, (int, long)):
                ids = [ids]
            if len(ids) == 1:
                self.addNeededFields(ids[0],vals,cr,uid)

        keys = vals.keys()
            
        email = False
        if 'email' in keys:
            email = vals['email']
            
        phone = False
        if 'phone' in keys:
            phone = vals['phone']
            
        fax=False
        if 'fax' in keys:
            fax = vals['fax']

        mobile = False
        if 'mobile' in keys:
            mobile = vals['mobile']

        lastname = False
        if 'lastname' in keys:
            lastname = vals['lastname']
            
        private_phone= False
        if 'private_phone' in keys:
            private_phone = vals['private_phone']
            
        
        # if name == False :
        #   raise osv.except_osv('Warning !', 'Please enter a contact name')
        if email :
            if re.match(
                        "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", 
                        email
                        ) == None :
                raise osv.except_osv(
                                        'Warning !', 
                                        'Please enter a valid e-mail'
                                    )
        if phone :
            if phone.startswith('+') == False :
                raise osv.except_osv(
                                    'Warning !', 
                                    'Please enter a valid phone number in'+\
                                    ' international format (i.e. leading +)'
                                )
        if fax :
            if fax.startswith('+') == False :
                raise osv.except_osv(
                                        'Warning !', 
                                        'Please enter a valid fax number '+\
                                        'in international format (i.e. leading +)'
                                    )
        if mobile :
            if mobile.startswith('+') == False :
                raise osv.except_osv(
                                        'Warning !', 
                                        'Please enter a valid mobile number '+\
                                        'in international format (i.e. leading +)'
                                    )
        if private_phone :
            if private_phone.startswith('+') == False :
                raise osv.except_osv(
                                        'Warning !', 
                                        'Please enter a valid private phone number'+\
                                        'in international format (i.e. leading +)'
                                    )
        if lastname == False and (ids == None or 'lastname' in keys):
            pass #We leave the test here just in case

    
    def getVals(self,att_name,key,vals,dico,uid,ids,cr, context={}) :
        "map to values to dict"
        ##To do improve revalidation here
        if key in vals.keys() and vals[key] <> False :
            dico[att_name] = vals[key]
        else :
            if context.has_key('init_mode') and context['init_mode'] :
                return False
            tmp = self.read(cr, uid, ids, [key], context={})
            if tmp.get(key,False) :
                dico[att_name] = tmp[key]
                
    def unUnicodize(self, indict) :
        "remove unicode data of modlist as unicode is not supported by python-ldap librairy"
        for key in indict :
            if  isinstance(indict[key], unicode) :
                try:
                    indict[key] = indict[key].encode()
                except Exception, e:
                    indict[key] = unicodedata.normalize(
                                                        "NFKD",
                                                        indict[key]
                                                        ).encode('ascii','ignore')
            if isinstance(indict[key], list) :
                nonutfArray = []
                for val in indict[key] :
                    if  isinstance(val, unicode) :
                        try:
                            val = val.encode()
                        except Exception, e:
                            val = unicodedata.normalize(
                                                        "NFKD",
                                                        val
                                                        ).encode('ascii','ignore')
                    nonutfArray.append(val)
                indict[key] = nonutfArray
         

    def addNeededFields(self,id,vals,cr,uid):   
        keys = vals.keys()

        previousvalue = self.browse(cr,uid,[id])[0]     
        
        
        if not 'partner_id' in keys :
            vals['partner_id'] = previousvalue.partner_id.id
            
        if not 'email' in keys:
            vals['email'] = previousvalue.email
            
        if not 'phone' in keys:
            vals['phone'] = previousvalue.phone
            
        if not 'fax' in keys:
            vals['fax'] = previousvalue.fax

        if not 'mobile' in keys:
            vals['mobile'] = previousvalue.mobile
            
        if not 'firstname' in keys:
            vals['firstname'] = previousvalue.firstname

        if not 'lastname' in keys:
            vals['lastname'] = previousvalue.lastname
            
        if not 'private_phone' in keys:
            vals['private_phone'] = previousvalue.private_phone
            
        if not 'street' in keys:
            vals['street'] = previousvalue.street
            
        if not 'street2' in keys:
            vals['street2'] = previousvalue.street2

        
    def mappLdapObject(self,id,vals,cr,uid,context):
        "Mapp ResPArtner adress to moddlist"
        self.addNeededFields(id,vals,cr,uid)
        conn = self.getconn(cr, uid, {})
        keys = vals.keys()
        partner_obj=self.pool.get('res.partner')
        part_name = partner_obj.browse(cr,uid,vals['partner_id']).name
        vals['partner'] = part_name
        cn = ''
        if 'lastname' in keys and 'firstname' in keys \
            and vals['firstname'] <> False \
            and vals['lastname'] <> False:
            cn = vals['lastname'] +' '+ vals['firstname']
        elif (('lastname' not in keys) or ('lastname' in keys \
            and vals['lastname'] == False)) and 'firstname' in keys \
            and vals['firstname'] <> False:
            cn = part_name + ' ' + vals['firstname']
        elif 'lastname' in keys and vals['lastname'] <> False \
            and (('firstname' not in keys) \
            or ('firstname' in keys and vals['firstname'] == False)) :
            cn = vals['lastname']
        else:
            cn = part_name
        if not vals['lastname'] :
            vals['lastname'] = part_name
        contact_obj = {
        'objectclass' : ['inetOrgPerson'],
        'uid': ['terp_'+str(id)],
        'ou':[conn.OU],
        'cn':[cn],
        'sn':[vals['lastname']]
        }
        if not vals['street']:
            vals['street'] = ''

        if not vals['street2']:
            vals['street2'] = ''
        street_key = 'street'
        if self.getconn(cr, uid, {}).ACTIVDIR :
            #ENTERING THE M$ Realm And it sucks
            #We manage the address
            street_key = 'streetAddress'
            contact_obj[street_key] = vals['street'] + "\r\n" + vals['street2']
            #we modifiy the class
            contact_obj['objectclass'] = ['top','person','organizationalPerson','inetOrgPerson','user']
            #we handle the country
            if 'country_id' in vals.keys() and vals['country_id'] :
                country =  self.browse(
                                        cr, 
                                        uid, 
                                        id
                                    ).country_id
                if country :
                    vals['country_id'] = country.name
                    vals['c'] = country.code
                else : 
                    vals['country_id'] = False
                    vals['c'] = False
            if vals.get('country_id', False) :
                self.getVals('co','country_id', vals, contact_obj, uid, id, cr, context)
                self.getVals('c','c', vals, contact_obj, uid, id, cr, context)
            #we compute the diplay name
            vals['display'] = '%s %s'%(vals['partner'], contact_obj['cn'][0])
            #we get the title
            if self.browse(cr, uid, id).function :
                contact_obj['description'] = self.browse(cr, uid, id).function.name
            #we replace carriage return 
            if vals.get('comment', False):
                vals['comment'] = vals['comment'].replace("\n","\r\n")
            #Active directory specific fields
            self.getVals('company','partner' ,vals, contact_obj, uid, id, cr, context)
            self.getVals('info','comment' ,vals, contact_obj, uid, id, cr, context)
            self.getVals('displayName','partner' ,vals, contact_obj, uid, id, cr, context)
            ##Web site management
            if self.browse(cr, uid, id).partner_id.website:
                vals['website'] = self.browse(cr, uid, id).partner_id.website
                self.getVals('wWWHomePage','website' ,vals, contact_obj, uid, id, cr, context)
                del(vals['website'])
            self.getVals('title','title' ,vals, contact_obj, uid, id, cr, context)        
        else :
            contact_obj[street_key] = vals['street'] + "\n" + vals['street2']
            self.getVals('o','partner' ,vals, contact_obj, uid, id, cr, context)
            
        #Common attributes    
        self.getVals('givenName', 'firstname',vals, contact_obj, uid, id, cr, context)
        self.getVals('mail', 'email',vals, contact_obj, uid, id, cr, context)
        self.getVals('telephoneNumber', 'phone',vals, contact_obj, uid, id, cr, context)
        self.getVals('l', 'city',vals, contact_obj, uid, id, cr, context)
        self.getVals('facsimileTelephoneNumber', 'fax',vals, contact_obj, uid, id, cr, context)
        self.getVals('mobile', 'mobile',vals, contact_obj, uid, id, cr, context)
        self.getVals('homePhone', 'private_phone',vals, contact_obj, uid, id, cr, context)
        self.getVals('postalCode', 'zip',vals, contact_obj, uid, id, cr, context)
        self.unUnicodize(contact_obj)
        return contact_obj
    
    def saveLdapContact(self,id,vals,cr,uid,context):
        "save openerp adress to ldap"
        contact_obj = self.mappLdapObject(id,vals,cr,uid,context)
        conn = self.connectToLdap(cr,uid,context={})
        try:
            if self.getconn(cr, uid, context).LDAP_SERVER:
                conn.connexion.add_s(
                                        "CN=%s,OU=%s,%s"%(contact_obj['cn'][0], conn.OU, conn.CONTACT_DN), 
                                        ldap.modlist.addModlist(contact_obj)
                                    )  
            else:
                conn.connexion.add_s(
                                        "uid=terp_%s,OU=%s,%s"%(str(id), conn.OU, conn.CONTACT_DN), 
                                        ldap.modlist.addModlist(contact_obj)
                                    )
        except Exception, e:
            raise e
        conn.connexion.unbind_s()
        
    def updateLdapContact(self,id,vals,cr,uid,context):
        "update an existing contact with the data of OpenERP"
        conn = self.connectToLdap(cr,uid,context={})
        try:
            old_contatc_obj = self.getLdapContact(conn,id)
        except ldap.NO_SUCH_OBJECT:
            self.saveLdapContact(id,vals,cr,uid,context)
            return
        contact_obj = self.mappLdapObject(id,vals,cr,uid,context)
        if conn.ACTIVDIR:
            modlist = []
            for key, val in contact_obj.items() :
               if key in ('cn','uid','objectclass') :
                   continue
               if isinstance(val, list):
                   val = val[0]
               modlist.append((ldap.MOD_REPLACE, key, val))
        else :
            modlist = ldap.modlist.modifyModlist(old_contatc_obj[1], contact_obj)

        try:
            conn.connexion.modify_s(old_contatc_obj[0], modlist)
            conn.connexion.unbind_s()
        except Exception, e:
            raise e
            
    def removeLdapContact(self,id,cr,uid):
        "Remove a contact from ldap"
        conn = self.connectToLdap(cr,uid,context={})
        to_delete = None
        try:
            to_delete = self.getLdapContact(conn,id)
        except ldap.NO_SUCH_OBJECT:
            print 'no object to delete in ldap'
        except Exception, e :
            raise e
        try:
            if to_delete :
                conn.connexion.delete_s(to_delete[0])
                conn.connexion.unbind_s()
        except Exception, e:
            raise e
        
    def getLdapContact(self, conn, id):
        result = conn.connexion.search_ext_s(
                                                "ou=%s,%s"%(conn.OU,conn.CONTACT_DN),
                                                ldap.SCOPE_SUBTREE,
                                                "(&(objectclass=*)(uid=terp_"+str(id)+"))"
                                            )
        if len(result) == 0:
            raise ldap.NO_SUCH_OBJECT
        return result[0]
        
    def ldaplinkactive(self,cr,uid,context):
        "Check if ldap is activated for this company"
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(cr, uid,user.company_id.id, context=context)
        return company.ldap_active
        
    def getconn(self, cr, uid, context) :
        "LdapConnMApper"
        if not self.ldapMapper :
            self.ldapMapper = LdapConnMApper(cr, uid, self)
        return self.ldapMapper   
          
    def connectToLdap(self, cr, uid, context):
        "Reinisialize ldap connection"
        #getting ldap pref
        if not self.ldapMapper :
            self.getconn(cr, uid, context)
        self.ldapMapper.get_connexion()
        return self.ldapMapper

            
class Ldap_partner(osv.osv):
    name = "contact_to_ldap.ldap_partner"
    _inherit = ('res.partner')
    
    def unlink(self, cr, uid, ids):
        obj = self.pool.get('res.partner.address')
        if isinstance(ids, (int, long)):
            ids = [ids]
        obj_ids = obj.search(cr,uid, [('partner_id','in',ids)])
        for address in obj.browse(cr,uid,obj_ids):
            address.unlink(cr,uid,address.id)
        return super(Ldap_partner, self).unlink(cr, uid, ids)
Contact_to_ldap_addressLdap()
Ldap_partner()
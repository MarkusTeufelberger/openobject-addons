# -*- coding: utf-8 -*- 
##############################################################################
#
# @author Bessi Nicolas
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
import time
from mx import DateTime
import netsvc
import string


from osv import osv, fields
import time
from mx import DateTime
import netsvc
import string

class ResPartnerAdressCategory(osv.osv):
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = self.name_get(cr, uid, ids)
        return dict(res)
    def _check_recursion(self, cr, uid, ids):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from res_partner_address_category\
             where id in ('+','.join(map(unicode,ids))+')')
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True
        
    

    _description='Partner address Categories'
    _name = 'res.partner.address.category'
    _columns = {
        'name': fields.char('Category Name', required=True, size=64),
        'parent_id': fields.many2one('res.partner.address.category', 'Parent Category', select=True),
        'complete_name': fields.function(_name_get_fnc, method=True, type="char", string='Name'),
        'child_ids': fields.one2many('res.partner.address.category', 'parent_id', 'Childs Category'),
        'active' : fields.boolean('Active'),
    }
    _constraints = [
        (_check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
    _defaults = {
        'active' : lambda *a: 1,
    }
    _order = 'parent_id,name'
ResPartnerAdressCategory()


#--------------------------------------------------------------------------------------------------------
# Adresse contact, split name in fct => first name + last name, recode name get and name search !
#--------------------------------------------------------------------------------------------------------
class ResPartnerAddress(osv.osv):
    _name = "res.partner.address"
    _inherit = "res.partner.address"
    
    # Gest the name (lastname + firstname), otherwise, street1 + street2 -> use in form
    def name_get(self, cr, uid, ids, context={}):
        logger = netsvc.Logger()
        if not len(ids):
            return []
        reads = self.read(
                            cr,
                            uid, 
                            ids, 
                            [
                                'lastname',
                                'firstname',
                                'street',
                                'street2',
                                'city',
                                'po_box', 
                                'partner_id'
                            ], 
                            context
                        )
        res = []
        for record in reads:
            if context.get('contact_display', 'contact')=='partner' and record['partner_id']:
                part = self.pool.get('res.partner').browse(cr, uid, 
                    record['partner_id'][0])
                res.append((record['id'], part.name))
                continue
            if type(record['lastname']) is bool :
                record['lastname'] = ''
            if type(record['firstname']) is bool :
                record['firstname'] = ''
            name = record['lastname']
            if record['firstname']:
                name = name + ' ' + record['firstname']
            if not name and record['street']:
                name = record['street']
                if record['street2']:
                    name=name+' '+record['street2']
            if not name and record['city']:
                name = record['city']
            if not name and record['po_box']:
                name = record['po_box']
            if not name :
                name = 'N/A'
            res.append((record['id'], name))
        return res
    
    
        
    def init(self, cr):
        logger = netsvc.Logger()
        try:
            cr.execute('ALTER TABLE res_partner_address RENAME column name to lastname ;')
            logger.notifyChannel(
                                    'c2c_partner_address init',
                                    netsvc.LOG_INFO, 
                                    'try to ALTER TABLE res_partner_address RENAME '+\
                                    'column name to lastname ;'
                                ) 
        except Exception, e:
            cr.rollback()
            logger.notifyChannel(
                                    'c2c_partner_address init',
                                    netsvc.LOG_INFO,
                                    'Warning ! impossible to rename column name'+\
                                    ' into lastname, this is probabely aleready done'
                                )

    # Gest the name (lastname + firstname), otherwise '' -> use in report
    # def _amount_total(self, cr, uid, ids, name, args, context={}):
    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        # res = self.name_get(cr, uid, ids)
        #       return dict(res)
        logger = netsvc.Logger()
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['lastname','firstname'])
        res = []
        for record in reads:
            if type(record['lastname']) is bool :
                record['lastname'] = ''
            if type(record['firstname']) is bool :
                record['firstname'] = ''
            name = record['lastname']
            if record['firstname']:
                name = name + ' ' + record['firstname']
            if not name :
                name = ''
            res.append((record['id'], name))
        return dict(res)
    
    def search(self, cr, user, args, offset=0, limit=None, order=None,
            context=None, count=False):
        newargs=[]
        for ag in args:
            if ag[2]:
                newargs.append(ag)
        args=newargs
        
        return super(ResPartnerAddress,self).search(cr, user, args, offset, limit,
                order, context=context, count=count)
    
    def name_search(self, cr, user, obj, name, args, context={}, limit=None):
        res = []
        whereclause = ''
        logger = netsvc.Logger()
        if type(args) != list:
            for i in name :
                if i[0] and i[1] and i[2]:
                    whereclause += "AND %s %s %s "%(i[0],i[1],i[2])
            arg = obj
        else :
            arg = args[0][2]
        if not arg :
            arg = ''
        cr.execute('select version()')
        vers = cr.fetchone()[0]
        
        if vers.startswith('PostgreSQL 8.3'):
            #postgres 8.3 !!! Yet the to ascii function is bugy we have to wait for the correction. 
            #in order to have accent insensitve search
            cr.execute("""select id from res_partner_address where (lastname ~* '.*%s.*' or firstname  ~* '.*%s.*') """%(arg,arg) + whereclause) 
            res = cr.fetchall()
        elif vers.startswith('PostgreSQL 8.0') or \
             vers.startswith('PostgreSQL 8.1') or \
             vers.startswith('PostgreSQL 8.2'):
            #postgres 8.0 to 8.2
            cr.execute("""select id from res_partner_address where \
            (to_ascii(convert( lastname, 'UTF8', 'LATIN1'),'LATIN-1')  ~* '.*%s.*' \
            or to_ascii(convert( firstname, 'UTF8', 'LATIN1'),'LATIN-1')  ~* '.*%s.*') """%(arg,arg) + whereclause) 
            res = cr.fetchall()
            
        # search in partner name to know if we are searching partner...
        partner_obj=self.pool.get('res.partner')
        partner_res=partner_obj.name_search(cr,user, obj,[],'ilike',context)
        # If we encounter no address -> take found partners -> we probably search on partner
        # If we encounter address and more than 80 partner, take only address, all partner is not an option
        # If we encounter address and less than 80 partner, 
        # take everything, we'll probably found what we're looking for in the list 
        if (not res) or (res and len(partner_res)<80):
            for p in partner_res:
                addresses=partner_obj.browse(cr,user,p[0]).address
                # Take each contact and add it to
                for add in addresses: #partner_obj.browse(cr,user,p[0])[0].address:
                    res.append(tuple([add.id]))

        if not res:
            # If not, return []
            if type(args) != list:
                return self.name_get(cr, user,[])
                
            return [('id','in',[])]
        if type(args) != list:
            return self.name_get(cr, user,[x[0] for x in res])
        return [('id', 'in', [x[0] for x in res])]
    
    def _street_default(self, cr, uid, context={}):
        if 'street' in context:
            t = context['street']
        else:
            t=''
        return t
    def _street2_default(self, cr, uid, context={}):
        if 'street2' in context:
            t = context['street2']
        else:
            t=''
        return t
    def _zip_default(self, cr, uid, context={}):

        if 'zip' in context:
            t = context['zip']
        else:
            t=''
        return t
    def _city_default(self, cr, uid, context={}):
        if 'city' in context:
            t = context['city']
        else:
            t=''
        return t
    def _po_box_default(self, cr, uid, context={}):
        if 'po_box' in context:
            t = context['po_box']
        else:
            t=''
        return t
    def _central_ph__default(self, cr, uid, context={}):
        if 'central_phone' in context:
            t = context['central_phone']
        else:
            t=''
        return t
    def _country_default(self, cr, uid, context={}):
        if 'country_id' in context:
            t = context['country_id']
        else:
            t=False
        return t
    
    _columns = {
        'name': fields.function(_name_get_fnc, method=True,  type="char", size=512, string='Name', store=False,fnct_search=name_search),
        'firstname' : fields.char('First name', size=256),
        'lastname' : fields.char('Last name', size=256),
        'private_phone' :fields.char('Private phone', size=128),
        'central_phone' :fields.char('Central phone', size=128),
        'private_emails': fields.char('Private E-Mail', size=128),
        'po_box' :fields.char('P.O Box', size=128),
        'category_id': fields.many2many('res.partner.address.category', 'res_partner_address_category_rel', 'adress_id', 'category_id', 'Adress categories'),
        'active2': fields.boolean('Active'),
        'picture': fields.binary('Picture'),
        'comment': fields.text('Notes'),
    }
    _defaults = {
        'active2': lambda *a: 1,
        'street': _street_default,
        'street2': _street2_default,
        'zip': _zip_default,
        'city': _city_default,
        'po_box': _po_box_default,
        'central_phone': _central_ph__default,
        'country_id': _country_default,
    }


ResPartnerAddress()

class ResPartner(osv.osv):
    _inherit = "res.partner"
        
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        if name:
            ids = self.search(cr, uid, [('ref', 'ilike', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    # Take the reference address for each partner
    # rules: - if only one address => take it
    #        - Otherwise take the default address (markes as default)
    #
    # Note: if there is more than one default addresse, take the first found
    #       We'll consider that normally there is only one default address !
    #       if there no default adresse, but one of an other type take the firstone
    # Return: {partner_id:browse record partner_address}
    def _address_get(self,cr, uid, ids, context={}, ptype='default'):
        partner_lists=self.pool.get('res.partner').browse(cr,uid,ids)
        res={}
        for partner in partner_lists:
            # Check the address => if only one, take it
            if len(partner.address) ==1:
                res[partner.id]=partner.address
            elif len(partner.address)>1:
                for address in partner.address:
                    if address.type == ptype:
                        #if partner already has adrees=> don't update it
                        if partner.id not in res.keys():
                            res[partner.id]=address
                # if empty => tke the first insteed of nothing
                if partner.id not in res.keys():
                    if partner.address[0]:
                        res[partner.id]=partner.address[0]
            else:
                res[partner.id]=False
        return res

    # Get the value of an asked field for each partner
    # Return: {partner_id:value}
    def _field_value_get(self, cr, uid, ids,name, arg, context={}):
        res={}
        field_to_get=name[5:]
        # get the address for each partner
        partner_address_lists=self._address_get(cr,uid,ids,context)
        for id in ids:
            # no value in partnlist => return ''
            res[id]=''
            # prevent case just one address
            try:
                if len (partner_address_lists[id])==1:
                    value=partner_address_lists[id][0]
            except:
                value=partner_address_lists[id]
            
            if id in partner_address_lists.keys():
                if value:
                    # if country, take the name
                    if field_to_get=='country_id':
                        if value.country_id:
                            res[id]=tuple(self.pool.get('res.country').name_get(
                                                                        cr, 
                                                                        uid, 
                                                                        value.country_id.id, 
                                                                        context)[0]
                                                                    ) 
                        else:
                            res[id]=False
                    else:
                        if value.__getattr__(field_to_get):
                            val=value.__getattr__(field_to_get)
                            res[id]=unicode(val)
        return res

    def country_search(self, cr, user, obj, name, args,context={}):
        if not args:
            args=[]
        if not context:
            context={}
        matching_country_res=self.pool.get('res.country').name_search(cr, user, args[0][2])
        matching_country=[]
        for res in matching_country_res:
                matching_country.append(res[0])

        if matching_country:
            add_ids = self.pool.get('res.partner.address').search(cr, user, [('country_id', 'in', matching_country),('type','=','default')], context=context)
            add_objs=self.pool.get('res.partner.address').browse(cr,user,add_ids)
            ids=[]
            for add in add_objs:
                ids.append(add.partner_id.id)
            ids=list(set(ids))  
        else:
            ids = []
        
        return [('id','in',ids)]#self.name_get(cr, user, ids, context)

    def city_search(self, cr, user, obj, name, args,context={}):
        if not args:
            args=[]
        if not context:
            context={}
        add_ids = self.pool.get('res.partner.address').search(
                                                                cr, 
                                                                user, 
                                                                [
                                                                    ('city', 'like', args[0][2])
                                                                ], 
                                                                context=context
                                                            )
        add_objs=self.pool.get('res.partner.address').browse(cr,user,add_ids)
        ids=[]
        for add in add_objs:
            ids.append(add.partner_id.id)
        ids=list(set(ids))
        return [('id','in',ids)]
        


    _columns = {
        # Function field based on default address, or if only one, the one :)
        #-----------------
        'part_street': fields.function(
                                        _field_value_get, 
                                        method=True,
                                        type='char',
                                        size=200, 
                                        string='Street'
                                    ),
        'part_street2': fields.function(
                                        _field_value_get, 
                                        method=True, 
                                        type='char',
                                        size=200, 
                                        string='Street2'
                                    ),
        'part_po_box': fields.function(
                                        _field_value_get, 
                                        method=True, 
                                        type='char',
                                        size=200, 
                                        string='P.O. Box'
                                    ),
        'part_zip': fields.function(
                                        _field_value_get, 
                                        method=True, 
                                        type='char',
                                        size=24, 
                                        string='Zip'
                                    ),
        'part_city': fields.function(
                                        _field_value_get, 
                                        method=True, 
                                        type='char',
                                        size=200, 
                                        string='City',
                                        fnct_search=city_search
                                    ),
        'part_country_id': fields.function(
                                            _field_value_get, 
                                            method=True, 
                                            type='many2one',
                                            relation='res.country', 
                                            string='Country',
                                            fnct_search=country_search
                                            ),
                                            
        'part_central_phone': fields.function(
                                                _field_value_get, 
                                                method=True, 
                                                type='char',
                                                size=128, 
                                                string='Central phone'
                                            ),
    }
        
        
ResPartner()



class ResPartnerFunction(osv.osv):
    _inherit = 'res.partner.function'
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
            if not args:
                args=[]
            if not context:
                context={}
            if name:
                ids = self.search(
                                    cr, 
                                    uid, 
                                    [('code', 'ilike', name)] + args, 
                                    limit=limit, 
                                    context=context
                                )
                if not ids:
                    ids = self.search(
                                        cr, 
                                        uid, 
                                        [('name', 'ilike', name)] + args, 
                                        limit=limit, 
                                        context=context
                                    )
            else:
                ids = self.search(cr, uid, args, limit=limit, context=context)
            return self.name_get(cr, uid, ids, context)
            
ResPartnerFunction()
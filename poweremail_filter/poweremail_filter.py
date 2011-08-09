# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008-2009 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                       General contacts <info@kndati.lv>
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields,osv
import netsvc
import time
import poweremail

from tools.translate import _

def _change_state(self, cr, uid, ids, field, field_type, field_id, sub_object_field_id, value1_char, value1_bool, \
        value1_int, value2_int, value1_float, value2_float, value1_date, value2_date, value1_datetime, value2_datetime, cond_value, value1_date_type, value2_date_type, value1_datetime_type, value2_datetime_type):
    data = {}
    if sub_object_field_id:
        field_name_id = self.pool.get('ir.model.fields').browse(cr, uid, field_id, {}).name
        subfield_name_id = self.pool.get('ir.model.fields').browse(cr, uid, sub_object_field_id, {}).name
        field_name = "%s.%s" % (field_name_id, subfield_name_id)
    elif field_id:
        field_name = self.pool.get('ir.model.fields').browse(cr, uid, field_id, {}).name
    else:
        field_name = 'count'
    if not field:
        return {'value':{},'state':False}
    else:
        cond_type = self.pool.get('poweremail.filter.rec_type').browse(cr, uid, field).value
        data['state'] = self.pool.get('poweremail.filter.rec_type').browse(cr, uid, field).type
        value = self.pool.get('poweremail.filter.rec_type').browse(cr, uid, field).value
        if data['state']!='[many2one]' and data['state']!='[one2many]' and data['state']!='[many2many]' and data['state']!='[boolean]' \
                and data['state']!='[char]' and data['state']!='[selection]':
            if value=='between' or value=='not between':
                data['state'] += '|2|'
            else:
                data['state'] += '|1|'
        if value!='between' and value!='not between':
            data['value2_int'] = 0
            data['value2_float'] = 0
            data['value2_date'] = ''
            data['value2_datetime'] = ''

        res = ''
        if cond_type == 'equal to':
            operator = ' == '
        elif cond_type == 'not equal to':
            operator = ' != '
        elif cond_type == 'greater than':
            operator = ' > '
        elif cond_type == 'less than':
            operator = ' < '
        elif cond_type == 'greater than or equal to':
            operator = ' >= '
        elif cond_type == 'less than or equal to':
            operator = ' <= '
        elif cond_type == 'like':
            operator = ' like '
        elif cond_type == 'ilike':
            operator = ' ilike '
        else:
            operator = ''

        if cond_type!='between' and cond_type!='not between':
            if field_type == '[char]' or field_type == '[selection]':
                res = field_name + operator + "'"+(value1_char and unicode(value1_char, "UTF-8") or '')+"'" or ''
            elif field_type == '[boolean]':
                res = field_name + operator + str(value1_bool) or ''
            elif field_type == '[integer]':
                res = field_name + operator + str(value1_int) or ''
            elif field_type == '[float]':
                res = field_name + operator + str(value1_float) or ''
            elif field_type == '[date]':
                value1_date = value1_date_type == 'fixed_date' and value1_date or value1_date_type
                res = field_name + operator + str(value1_date) or ''
            elif field_type == '[datetime]':
                res = field_name + operator + str(value1_datetime) or ''
        elif cond_type=='between':
            if field_type == '[integer]':
                res = '(' + field_name + ' >= ' + str(value1_int)+')'
                if value2_int != None:
                    res += ' and ('+field_name+ ' <= ' + str(value2_int)+')' or ''
            elif field_type == '[float]':
                res = '(' + field_name + ' >= ' + str(value1_float)+')'
                if value2_float != None:
                    res += ' and ('+field_name+ ' <= ' + str(value2_float)+')' or ''
            elif field_type == '[date]':
                res = '(' + field_name + ' >= ' + str(value1_date)+')'
                if value2_date:
                    res += ' and ('+field_name+ ' <= ' + str(value2_date)+')' or ''
            elif field_type == '[datetime]':
                res += '(' + field_name + ' >= ' + str(value1_datetime)+')'
                if value2_datetime:
                    res += ' and ('+field_name+ ' <= ' + str(value2_datetime)+')' or ''
        elif cond_type=='not between':
            if field_type == '[integer]':
                res = '(' + field_name + ' <= ' + str(value1_int)+')' or ''
                if value2_int != None:
                    res += ' and ('+field_name+ ' >= ' + str(value2_int)+')' or ''
            elif field_type == '[float]':
                res = '(' + field_name + ' <= ' + str(value1_float)+')'
                if value2_float != None:
                    res += ' and ('+field_name+ ' >= ' + str(value2_float)+')' or ''
            elif field_type == '[date]':
                res = '(' + field_name + ' <= \'' + str(value1_date)+'\')'
                if value2_date:
                    res += ' and ('+field_name+ ' >= \'' + str(value2_date)+'\')' or ''
            elif field_type == '[datetime]':
                res = '(' + field_name + ' <= \'' + str(value1_datetime)+'\')'
                if value2_datetime:
                    res += ' and ('+field_name+ ' >= \'' + str(value2_datetime)+'\')' or ''

        if cond_type=='in' or cond_type=='not in':
            res = field_name + ' ' + cond_type
            if cond_value and cond_value != None:
                res += ' ['+cond_value+']' or ''
        data['name'] = res
    return data


class rec_type(osv.osv):
    _name = "poweremail.filter.rec_type"
    _rec_name = "value"

    _columns = {
        'type': fields.char('Type', size=64, required=True),
        'value': fields.char('Value', size=64, required=True),
    }

rec_type()


class rec_filter(osv.osv):
    _name = 'poweremail.filter.rec_filter'

rec_filter()


class poweremail_cron(osv.osv):
    "Cron for sending Email"
    _name = "poweremail.filter"
    _description = 'Send automatically emails with filters'

    _columns = {
        'name': fields.char('Name', size=100, required=True, help='Name of the cron for sending Email.'),
        'template_id':fields.many2one('poweremail.templates', 'Template Poweremail', required=True),
        'model_id':fields.related('template_id', 'object_name', readonly=True, type='many2one',relation='ir.model', string='Model'),
        'ir_cron_id':fields.many2one('ir.cron', 'Cron', readonly=True),
        'manual': fields.boolean('Manual'),
        'mix_operator':fields.selection([
                ('and','And'),
                ('or','Or'),    
            ], 'Mix operator', states={'manual':[('readonly',False)]},
            help='Operator to mix the records obtained through the filters in the first tab and records calculated by the manual code.'),
        'source': fields.text('Source', states={'manual':[('readonly',False)]}),
        'active': fields.boolean('Active'),
        'rec_filter_ids': fields.one2many('poweremail.filter.rec_filter', 'pwfilter_id', 'Filters'),
        'last_send': fields.datetime('Last Send', required=True)
    }       

    _defaults = {
        'active': lambda *a: 1,
        'mix_operator': lambda *a: 'and',
        'last_send': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    def create_cron(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ircron = self.pool.get('ir.cron')
        value = {}
        for pwcron in self.browse(cr, uid, ids, context):
            values = {
                'name': pwcron.name,
                'user_id': uid,
                'active': True,
                'nextcall' : time.strftime('%Y-%m-%d %H:%M:%S'),   
                'model':'poweremail.filter',
                'function':'run_pwfilter_cron_scheduler',
                'args': '('+str(pwcron.id)+',)',
            }
            value = {'ir_cron_id' : ircron.create(cr, uid, values)}
            
        return self.write(cr, uid, ids, value, context)

    def delete_cron(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ir_cron_ids = []
        for pwcron in self.browse(cr, uid, ids, context):
            ir_cron_ids.append(pwcron.ir_cron_id.id)
        self.pool.get('ir.cron').unlink(cr, uid, ir_cron_ids)
        value = {'ir_cron_id' : ""}
        
        return self.write(cr, uid, ids, value, context)

    def search_records(self, cr, uid, id, context=None):
        pwfilter_cond_obj = self.pool.get('poweremail.filter.rec_filter_cond')
        pwcron = self.browse(cr, uid, id, context={})

        # Normal filter. Convert filters to OpenERP search criteria list
        oesearch = []
        first = True
        for filt in pwcron.rec_filter_ids:
            oes = pwfilter_cond_obj._get_oesearch(cr, uid, [x.id for x in filt.condition_id], context=context)

            if first:
                oesearch = oes
                first = False
            else:
                # Different filters are joined with AND operator
                oesearch = ['&'] + oes + oesearch
#        print oesearch
        ids = self.pool.get(pwcron.template_id.object_name.model).search(cr, uid, oesearch)
#        print "Normal filter ids", ids

        if pwcron.manual:
        # Manual filter
            ids_manual = []
            localspace = {"self":self,"cr":cr,"uid":uid,"ids":ids}
            exec pwcron.source in localspace
            ids_manual = localspace['ids']
#            print "Manual filter ids", ids_manual
            if pwcron.mix_operator == 'and':
                ids = filter(lambda x: x in ids, ids_manual)
            else: # mix_operator == 'or'
                ids = ids + filter(lambda x: x not in ids, ids_manual)

#        print "Filter ids", ids
        return ids

    def test_filters(self, cr, uid, ids, context=None):
        res = []
        for pwcron in self.browse(cr, uid, ids, context={}):
            try:
                r_ids = self.search_records(cr, uid, pwcron.id)
            except (SyntaxError, NameError, IndexError, AttributeError), exc:
                raise osv.except_osv(_('Error'), _('Manual filter error:\n') + str(exc))
            res += r_ids
        raise osv.except_osv(_('Information'),
            _('The filters have found the following records:\n%s') %
            ','.join([str(r) for r in res])
        )
        return True

    def send_emails(self, cr, uid, ids, context=None):
        logger = netsvc.Logger()
        res = []
        for pwcron in self.browse(cr, uid, ids, context={}):
            try:
                r_ids = self.search_records(cr, uid, pwcron.id)
            except (SyntaxError, NameError, IndexError, AttributeError), exc:
                raise osv.except_osv(_('Error'), _('Manual filter error:\n') + str(exc))
            res += r_ids
            #send emails from poweremail template
            self.pool.get('poweremail.templates').generate_mail(cr, uid, pwcron.template_id.id, r_ids)
        self.write(cr, uid, ids, {'last_send': time.strftime('%Y-%m-%d %H:%M:%S')})
        logger.notifyChannel('Poweremail Cron', netsvc.LOG_INFO, _('The following emails are generated for the filtered records:\n%s\nCheck these mails in the Out box.') % ','.join([str(r) for r in res]))
        return True

    def run_pwfilter_cron_scheduler(self, cr, uid, context=None):
        logger = netsvc.Logger()

        if type(context) not in [int, long]:
            logger.notifyChannel('Poweremail Cron', netsvc.LOG_INFO, "Error arguments in cron configuration")
            return False
        else:
            id = context
            pwcron_ids = self.search(cr, uid, [('id','=',id)])
            if not pwcron_ids:
                logger.notifyChannel('Poweremail Cron', netsvc.LOG_ERROR, 'Not avaible poweremail cron id %s' % id)
                return False
            else:
                logger.notifyChannel('Poweremail Cron', netsvc.LOG_INFO, "Filtered sendmail id %s" % id)
                pwcron = self.browse(cr, uid, id, context={})   
                try:
                    r_ids = self.search_records(cr, uid, pwcron.id)
                except (SyntaxError, NameError, IndexError, AttributeError), exc:
                    logger.notifyChannel('Poweremail Cron: Manual filter error id %s' % pwcron.id, netsvc.LOG_ERROR, str(exc))
                r_ids = self.search_records(cr, uid, id)
                #send emails
                self.pool.get('poweremail.templates').generate_mail(cr, uid, pwcron.template_id.id, r_ids)
                self.write(cr, uid, id, {'last_send': time.strftime('%Y-%m-%d %H:%M:%S')})
                return True

poweremail_cron()


class rec_filter(osv.osv):
    _name = "poweremail.filter.rec_filter"
    _inherit = 'poweremail.filter.rec_filter'
    _rec_name = "filters"

    def _get_field_type(self, cr, uid, ids, field_name, arg=None, context={}):
        res={}
        for p in self.browse(cr, uid, ids, context):
            if p.field_id:
                temp = p.field_id.ttype
                if temp == 'one2many' or temp == 'many2one' or temp == 'many2many':
                    temp = p.sub_object_field_id.ttype
                    res[p.id]='[%s]' % temp
                else:
                    res[p.id]='[%s]' % temp
            else:
                res[p.id]='[integer]'
        return res

    def _get_filters(self, cr, uid, ids, field, arg=None, context={}):
        res = {}
        obj = self.pool.get('poweremail.filter.rec_filter_cond')
        for p in self.browse(cr, uid, ids, context):
            temp = ''
            cond_ids = map(int, p.condition_id)
            if cond_ids == []:
                if p.field_id:
                    temp = p.field_id.name
                else:
                    temp = 'count'
            for r in obj.browse(cr, uid, cond_ids, context):
                if r.id == cond_ids[0]:
                    if len(cond_ids) > 1:
                        temp = '('+r.name+')'
                    elif not r.name:
                        temp = 'count'
                    else:
                        temp = r.name
                else:
                    temp += ' or ('+r.name+')'
            res[p.id] = temp
        return res

    _columns = {
        'filters': fields.function(_get_filters, method=True, string='Filters', type='char', size=128),
        'subfilters': fields.function(_get_filters, method=True, string='SubFilters', type='char', size=128),
        'pwfilter_id': fields.many2one('poweremail.filter', 'Poweremail Cron'),
        'field_id': fields.many2one('ir.model.fields', 'Field', domain="[('model_id', '=', parent.model_id),('ttype','!=','binary')]", states={'def':[('readonly',True)],'undef1':[('readonly',True)]}, required=True),
        'sub_object':fields.many2one(
                 'ir.model',
                 'Sub-model',
                 help='When a relation field is used this field'
                 ' will show you the type of field you have selected',
                 ),
        'sub_object_field_id':fields.many2one(
                 'ir.model.fields',
                 'Sub Field',
                 help="When you choose relationship fields "
                 "this field will specify the sub value you can use.",
                 states={'def':[('readonly',True)],'undef1':[('readonly',True)]}),
        'condition_id': fields.one2many('poweremail.filter.rec_filter_cond', 'rec_filter_id', 'Condition'),
        'field_type': fields.function(_get_field_type, method=True, string='Ttype', type='char'),
        'state': fields.selection([('def', 'Defined'),('undef1', 'Undefined'),('undef2', 'Undefined')], 'State', readonly=True),
        'var': fields.selection([('field', 'Field'),('count', 'Count')], 'Variable', states={'def':[('readonly',True)]}),
        'temp_field_id': fields.many2one('ir.model.fields', 'Temp Field', domain="[('model_id', '=', parent.model_id),('ttype','!=','selection'),('ttype','!=','binary')]"),
        'temp_var': fields.selection([('field', 'Field'),('count', 'Count')], 'Temp Variable'),
        'temp_sub_object': fields.many2one('ir.model', 'Temp SubModel'),
        'temp_sub_object_field_id': fields.many2one('ir.model.fields', 'Temp SubField'),
    }

    def change_field_type(self, cr, uid, ids, field, var, context):
        data = {}
        if not field:
            data['sub_object'] = False
            data['sub_object_field_id'] = False
            data['field_type'] = ''
            data['filters'] = ''
            return {'value':data}
        elif var == 'count':
            data['field_id'] = False
        else:
            field_obj = self.pool.get('ir.model.fields').browse(cr, uid, field, context)
            if field_obj.ttype in ['many2one', 'one2many', 'many2many']:
                res_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', field_obj.relation)], context=context)
                if res_ids:
                    data['sub_object'] = res_ids[0]
                    data['sub_object_field_id'] = False
            data['field_type'] = '['+field_obj.ttype+']'
            data['filters'] = field_obj.name
        return {'value':data}

    def change_sub_object_field_id(self, cr, uid, ids, sub_object, sub_object_field_id, context=None):
        if not sub_object or not sub_object_field_id:
            return {}
        data = {}
        field_obj = self.pool.get('ir.model.fields').browse(cr, uid, sub_object_field_id, context)
        data['sub_object_field_id'] = sub_object_field_id
        data['null_value'] = False
        data['field_type'] = '['+field_obj.ttype+']'
        data['subfilters'] = field_obj.name
        data['sub_object'] = sub_object

        return {'value':data}

#    def change_var(self, cr, uid, ids, field):
#        data = {}

#        if not field:
#            return {'value':{}}
#        elif field == 'count':
#            data['field_type'] = '[integer]'
#            data['field_id'] = False
#            data['state'] = 'undef1'
#        else:
#            data['field_type'] = ''
#            data['state'] = 'undef2'
#        return {'value':data}

    def change_condition(self, cr, uid, ids, condition_id, field_id, sub_object, sub_object_field_id, var, relation):
        data = {}
        temp = ''

        for r in condition_id:
            if r[2] and r[2] != {}:
                if r == condition_id[0]:
                    if len(condition_id) > 1:
                        temp = '('+r[2]['name']+')'
                    else:
                        temp = r[2]['name']
                else:
                    temp += ' or ('+r[2]['name']+')'
        data['filters'] = temp
        if relation:
            data['state'] = 'def'
        else:
            data['state'] = 'def'
        data['temp_field_id'] = field_id
        data['temp_sub_object'] = sub_object
        data['temp_sub_object_field_id'] = sub_object_field_id
        data['temp_var'] = var
        return {'value':data}

    def name_get(self, cr, user, ids, context={}):
        if not len(ids):
            return []
        res = []
        for r in self.read(cr, user, ids, ['pwfilter_id', 'field_id', 'calc_id']):
            if r['field_id']:
                if r['pwfilter_id']:
                    name = str(r['pwfilter_id'][1])
                    name +=', '
                else:
                    name = str(r['calc_id'][1])
                    name +=', '
                name += str(r['field_id'][1])
                res.append((r['id'], name))
        return res

    def create(self, cr, uid, vals, context={}):
        if not context:
            context={}
        vals=vals.copy()
        vals['state'] = 'def'
        vals['var'] = vals['temp_var']
        vals['field_id'] = vals['temp_field_id']
        vals['sub_object'] = vals['temp_sub_object']
        vals['sub_object_field_id'] = vals['temp_sub_object_field_id']
        c = context.copy()
        c['novalidate'] = True
        result = super(rec_filter, self).create(cr, uid, vals, c)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context={}
        for r in self.browse(cr, uid, ids, {}):
            vals=vals.copy()
            vals['state'] = 'def'
        return super(rec_filter, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context):
        conditions = map(int, self.browse(cr, uid, ids[0], {}).condition_id)
        self.pool.get('poweremail.filter.rec_filter_cond').unlink(cr, uid, conditions, context)
        osv.osv.unlink(self, cr, uid, ids, context)
        return True

    _defaults = {
        'var' : lambda *a: 'field',
        'state' : lambda *a: 'undef2',
        'field_type' : lambda *a: '[integer]',
    }

rec_filter()


class rec_filter_cond(osv.osv):
    _name = "poweremail.filter.rec_filter_cond"
    _rec_name = "rec_filter_id"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        result = super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context)
        return result

    def _change_state(self, cr, uid, ids, field, arg=None, context={}):
        res = {}
        for p in self.browse(cr, uid, ids, context):
            if p:
                filter_id = p.rec_filter_id
                ctype = filter_id.field_type
                value = p.cond_type.value
                if ctype!='[many2one]' and ctype!='[one2many]' and ctype!='[many2many]' and ctype!='[boolean]' \
                        and ctype!='[char]' and ctype!='[selection]':
                    if value=='between' or value=='not between':
                        res[p.id] = ctype + '|2|'
                    else:
                        res[p.id] = ctype + '|1|'
                else:
                    res[p.id] = ctype
        return res

    def _get_name(self, cr, uid, ids, field, arg=None, context={}):
        res = {}
        for r in self.browse(cr, uid, ids, context):
            filter_id = r.rec_filter_id
            model = 'poweremail.filter.rec_filter'
            if filter_id.var != 'count':
                rec_filter_obj = self.pool.get('poweremail.filter.rec_filter')
                rec_filter = rec_filter_obj.browse(cr, uid, r.rec_filter_id.id, context)
                sub_object_field_id = rec_filter.sub_object_field_id
                if sub_object_field_id:
                    submodel_field_name = self.pool.get('ir.model.fields').browse(cr, uid, sub_object_field_id.id, context)
                    field = "%s.%s" % (filter_id.field_id.name,submodel_field_name.name)
                else:
                    field = filter_id.field_id.name
                filter_field_type = self.pool.get(model).browse(cr, uid, filter_id.id, {}).field_type
            else:
                field = 'count'
                filter_field_type = '[integer]'
            if r.cond_type.value == 'equal to':
                operator = ' == '
            elif r.cond_type.value == 'not equal to':
                operator = ' != '
            elif r.cond_type.value == 'greater than':
                operator = ' > '
            elif r.cond_type.value == 'less than':
                operator = ' < '
            elif r.cond_type.value == 'greater than or equal to':
                operator = ' >= '
            elif r.cond_type.value == 'less than or equal to':
                operator = ' <= '
            elif r.cond_type.value == 'like':
                operator = ' like '
            elif r.cond_type.value == 'ilike':
                operator = ' ilike '
            else:
                operator = ''
                
            if r.cond_type.value!='between' and r.cond_type.value!='not between':
                if filter_field_type == '[char]' or filter_field_type == '[selection]':
                    res[r.id] = field + operator + "'"+r.value1_char+"'" or ''
                elif filter_field_type == '[boolean]':
                    res[r.id] = field + operator + str(r.value1_bool) or ''
                elif filter_field_type == '[integer]':
                    res[r.id] = field + operator + str(r.value1_int) or ''
                elif filter_field_type == '[float]':
                    res[r.id] = field + operator + str(r.value1_float) or ''
                elif filter_field_type == '[date]':
                    value1_date = r.value1_date_type == 'fixed_date' and r.value1_date or r.value1_date_type
                    res[r.id] = field + operator + str(value1_date) or ''
                elif filter_field_type == '[datetime]':
                    value1_datetime = r.value1_datetime_type == 'fixed_date' and r.value1_datetime or r.value1_datetime_type
                    res[r.id] = field + operator + str(value1_datetime) or ''
            elif r.cond_type.value=='between':
                if filter_field_type == '[integer]':
                    res[r.id] = '(' + field + ' >= ' + str(r.value1_int)+')'
                    if r.value2_int != None:
                        res[r.id] += ' and ('+field+ ' <= ' + str(r.value2_int)+')' or ''
                elif filter_field_type == '[float]':
                    res[r.id] = '(' + field + ' >= ' + str(r.value1_float)+')'
                    if r.value2_float != None:
                        res[r.id] += ' and ('+field+ ' <= ' + str(r.value2_float)+')' or ''
                elif filter_field_type == '[date]':
                    value1_date = r.value1_date_type == 'fixed_date' and r.value1_date or r.value1_date_type
                    value2_date = r.value2_date_type == 'fixed_date' and r.value2_date or r.value2_date_type
                    res[r.id] = '(' + field + ' >= ' + str(value1_date)+')'
                    if value2_date:
                        res[r.id] += ' and ('+field+ ' <= ' + str(value2_date)+')' or ''
                elif filter_field_type == '[datetime]':
                    value1_datetime = r.value1_datetime_type == 'fixed_date' and r.value1_datetime or r.value1_datetime_type
                    value2_datetime = r.value2_datetime_type == 'fixed_date' and r.value2_datetime or r.value2_datetime_type
                    res[r.id] = '(' + field + ' >= ' + str(value1_datetime)+')'
                    if value2_datetime:
                        res[r.id] += ' and ('+field+ ' <= ' + str(value2_datetime)+')' or ''
            elif r.cond_type.value=='not between':
                if filter_field_type == '[integer]':
                    res[r.id] = '(' + field + ' <= ' + str(r.value1_int)+')' or ''
                    if r.value2_int != None:
                        res[r.id] += ' and ('+field+ ' >= ' + str(r.value2_int)+')' or ''
                elif filter_field_type == '[float]':
                    res[r.id] = '(' + field + ' <= ' + str(r.value1_float)+')'
                    if r.value2_float != None:
                        res[r.id] += ' and ('+field+ ' >= ' + str(r.value2_float)+')' or ''
                elif filter_field_type == '[date]':
                    value1_date = r.value1_date_type == 'fixed_date' and r.value1_date or r.value1_date_type
                    value2_date = r.value2_date_type == 'fixed_date' and r.value2_date or r.value2_date_type
                    res[r.id] = '(' + field + ' <= \'' + str(value1_date)+'\')'
                    if value2_date:
                        res[r.id] += ' and ('+field+ ' >= \'' + str(value2_date)+'\')' or ''
                elif filter_field_type == '[datetime]':
                    value1_datetime = r.value1_datetime_type == 'fixed_date' and r.value1_datetime or r.value1_datetime_type
                    value2_datetime = r.value2_datetime_type == 'fixed_date' and r.value2_datetime or r.value2_datetime_type
                    res[r.id] = '(' + field + ' <= \'' + str(value1_datetime)+'\')'
                    if value2_datetime:
                        res[r.id] += ' and ('+field+ ' >= \'' + str(value2_datetime)+'\')' or ''
    
            if r.cond_type.value=='in' or r.cond_type.value=='not in':
                res[r.id] = field + ' ' + r.cond_type.value
                if r.cond_value and r.cond_value != None:
                    res[r.id] += ' ['+r.cond_value+']' or ''
        
        return res


    def _get_oesearch(self, cr, uid, ids, context={}):
        # Computes OpenERP search criteria list from the filter conditions
        res = []
        first = True
        for r in self.browse(cr, uid, ids, context):
            filter_id = r.rec_filter_id
            model = 'poweremail.filter.rec_filter'
            pwfilter = self.pool.get('poweremail.filter').browse(cr, uid, r.rec_filter_id.pwfilter_id.id)

            last_send1 = pwfilter.last_send[:10] #date
            last_send2 = pwfilter.last_send #datetime
            today1 = time.strftime('%Y-%m-%d') #date
            today2 = time.strftime('%Y-%m-%d %H:%M:%S') #datetime

            if filter_id.var != 'count':
                rec_filter_obj = self.pool.get('poweremail.filter.rec_filter')
                rec_filter = rec_filter_obj.browse(cr, uid, r.rec_filter_id.id, context)
                sub_object_field_id = rec_filter.sub_object_field_id
                if sub_object_field_id:
                    submodel_field_name = self.pool.get('ir.model.fields').browse(cr, uid, sub_object_field_id.id, context)
                    field = "%s.%s" % (filter_id.field_id.name,submodel_field_name.name)
                else:
                    field = filter_id.field_id.name
                filter_field_type = self.pool.get(model).browse(cr, uid, filter_id.id, {}).field_type
            else:
                field = 'count'
                filter_field_type = '[integer]'
            if r.cond_type.value == 'equal to':
                operator = '='
            elif r.cond_type.value == 'not equal to':
                operator = '!='
            elif r.cond_type.value == 'greater than':
                operator = '>'
            elif r.cond_type.value == 'less than':
                operator = '<'
            elif r.cond_type.value == 'greater than or equal to':
                operator = '>='
            elif r.cond_type.value == 'less than or equal to':
                operator = '<='
            elif r.cond_type.value == 'like':
                operator = 'like'
            elif r.cond_type.value == 'ilike':
                operator = 'ilike'
            else:
                operator = ''
                
            if r.cond_type.value!='between' and r.cond_type.value!='not between':
                if filter_field_type == '[char]' or filter_field_type == '[selection]':
                    cond = [(field, operator, r.value1_char)]
                elif filter_field_type == '[boolean]':
                    cond = [(field, operator, r.value1_bool)]
                elif filter_field_type == '[integer]':
                    cond = [(field, operator, r.value1_int)]
                elif filter_field_type == '[float]':
                    cond = [(field, operator, r.value1_float)]
                elif filter_field_type == '[date]':
                    value1_date = r.value1_date_type == 'fixed_date' and r.value1_date or r.value1_date_type == 'last_send' and last_send1 or today1
                    cond = [(field, operator, value1_date)]
                elif filter_field_type == '[datetime]':
                    value1_datetime = r.value1_datetime_type == 'fixed_date' and r.value1_datetime or r.value1_datetime_type == 'last_send' and last_send2 or today2
                    cond = [(field, operator, value1_datetime)]
            elif r.cond_type.value=='between':
                if filter_field_type == '[integer]':
                    cond = [(field, '>=', r.value1_int)]
                    if r.value2_int != None:
                        cond = ['&', (field, '<=', r.value2_int)] + cond
                elif filter_field_type == '[float]':
                    cond = [(field, '>=', r.value1_float)]
                    if r.value2_float != None:
                        cond = ['&', (field, '<=', r.value2_float)] + cond
                elif filter_field_type == '[date]':
                    value1_date = r.value1_date_type == 'fixed_date' and r.value1_date or r.value1_date_type == 'last_send' and last_send1 or today1
                    value2_date = r.value2_date_type == 'fixed_date' and r.value2_date or r.value2_date_type == 'last_send' and last_send1 or today1
                    cond = [(field, '>=', value1_date)]
                    if value2_date:
                        cond = ['&', (field, '<=', value2_date)] + cond
                elif filter_field_type == '[datetime]':
                    value1_datetime = r.value1_datetime_type == 'fixed_date' and r.value1_datetime or r.value1_datetime_type == 'last_send' and last_send2 or today2
                    value2_datetime = r.value2_datetime_type == 'fixed_date' and r.value2_datetime or r.value2_datetime_type == 'last_send' and last_send2 or today2
                    cond = [(field, '>=', value1_datetime)]
                    if value2_datetime:
                        cond = ['&', (field, '<=', value2_datetime)] + cond
            elif r.cond_type.value=='not between':
                if filter_field_type == '[integer]':
                    cond = [(field, '<=', r.value1_int)]
                    if r.value2_int != None:
                        cond = ['&', (field, '>=', r.value2_int)] + cond
                elif filter_field_type == '[float]':
                    cond = [(field, '<=', r.value1_float)]
                    if r.value2_float != None:
                        cond = ['&', (field, '>=', r.value2_float)] + cond
                elif filter_field_type == '[date]':
                    value1_date = r.value1_date_type == 'fixed_date' and r.value1_date or r.value1_date_type
                    value2_date = r.value2_date_type == 'fixed_date' and r.value2_date or r.value2_date_type
                    cond = [(field, '<=', value1_date)]
                    if value2_date:
                        cond = ['&', (field, '>=', value2_date)] + cond
                elif filter_field_type == '[datetime]':
                    value1_datetime = r.value1_datetime_type == 'fixed_date' and r.value1_datetime or r.value1_datetime_type
                    value2_datetime = r.value2_datetime_type == 'fixed_date' and r.value2_datetime or r.value2_datetime_type
                    cond = [(field, '<=', r.value1_datetime)]
                    if value2_datetime:
                        cond = ['&', (field, '>=', value2_datetime)] + cond
    
            if r.cond_type.value=='in' or r.cond_type.value=='not in':
                if r.cond_value and r.cond_value != None:
                    cond = [(field, r.cond_type.value, [int(x) for x in r.cond_value.split(',')])]

            if first:
                res = cond
                first = False
            else:
                # Conditions of the same filter are joined with OR operator
                res = ['|'] + cond + res

        return res

    _columns = {
        'name': fields.function(_get_name, method=True, string='Filter coditions', type='char', size=128),
        'rec_filter_id': fields.many2one('poweremail.filter.rec_filter', 'Filter'),
        'cond_type': fields.many2one('poweremail.filter.rec_type', 'Condition type', domain="[('type', '=', parent.field_type)]"),
        'state': fields.function(_change_state, method=True, string='State', type='char', size=128),
        'cond_value': fields.char('Condition value', size=128, states={'[many2many]':[('readonly',False),('required',True)],'[many2one]':[('readonly',False),('required',True)],'[one2many]':[('readonly',False),('required',True)]},readonly=True),
        'value1_char': fields.char('Char', size=256, states={'[char]':[('readonly',False),('required',True)],'[selection]':[('readonly',False),('required',True)]}, readonly=True),
        'value1_bool': fields.boolean('Boolean', states={'[boolean]':[('readonly',False),('required',True)]}, readonly=True),
        'value1_int': fields.integer('Integer1', states={'[integer]|1|':[('readonly',False),('required',True)],'[integer]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value2_int': fields.integer('Integer2', states={'[integer]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value1_float': fields.float('Float1', states={'[float]|1|':[('readonly',False)],'[float]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value2_float': fields.float('Float2', states={'[float]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value1_date_type': fields.selection([('today', 'Today'),('last_send', 'Last Send'),('fixed_date', 'Fixed Date'),], 'Date Type', states={'[date]|1|':[('readonly',False),('required',True)],'[date]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value1_date': fields.date('Date1'),
        'value2_date_type': fields.selection([('today', 'Today'),('last_send', 'Last Send'),('fixed_date', 'Fixed Date'),], 'Date Type', states={'[date]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value2_date': fields.date('Date2'),
        'value1_datetime_type': fields.selection([('today', 'Today'),('last_send', 'Last Send'),('fixed_date', 'Fixed Date'),], 'Date Type', states={'[datetime]|1|':[('readonly',False),('required',True)],'[datetime]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value1_datetime': fields.datetime('DateTime1'),
        'value2_datetime_type': fields.selection([('today', 'Today'),('last_send', 'Last Send'),('fixed_date', 'Fixed Date'),], 'Date Type', states={'[datetime]|2|':[('readonly',False),('required',True)]}, readonly=True),
        'value2_datetime': fields.datetime('DateTime2'),
    }

    def on_change_state(self, cr, uid, ids, field, field_type, field_id, sub_object_field_id, value1_char, value1_bool, \
            value1_int, value2_int, value1_float, value2_float, value1_date, value2_date, value1_datetime, value2_datetime, cond_value, value1_date_type, value2_date_type, value1_datetime_type, value2_datetime_type):
        data = _change_state(self, cr, uid, ids, field, field_type, field_id, sub_object_field_id, value1_char, value1_bool, \
            value1_int, value2_int, value1_float, value2_float, value1_date, value2_date, value1_datetime, value2_datetime, cond_value, value1_date_type, value2_date_type, value1_datetime_type, value2_datetime_type)
        return {'value':data}

rec_filter_cond()

# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai (gdukai@gmail.com)
#    Copyright (C) 2009 Ville D'ouro (<http://villedouro.com.br>). All Rights Reserved
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
#    Author: Cloves J. G. de Almeida <cjalmeida@gvmail.br>
#
##############################################################################

"""
This module add xml serialization and deserialization capabilities to osv.osv objects
"""
import logging
from lxml import etree
from lxml import objectify

from osv import osv
from tools.translate import _

log = logging.getLogger('osv_xml')

class DeserializationError(Exception):
    def __init__(self, rule, orig_exception):
        self.message = _("Error while processing binding rule %s") % rule
        self.orig_exception = orig_exception
    def __str__(self):
        return self.message

def obj_to_xml(obj, cr, uid, ids, root_tag, bindings, context=None):
    """
    Convert an OpenObject object into a xml representation.

    The bindings argument is a list of strings or tuples of the following form:

      * 'colname' or ('colname')
          Creates a element named 'colname' bound to 'colname' column

      * ('colname', 'element')
          Creates a element named 'element' bound to 'colname' column

      * ('colname', 'element', 'subcol')
          For relations, creates a element named 'element' bound to 'colname' column
          but instead of object id, uses subcol as value. The subcol must be unique,
          else the deserializer will return the ID of the first match.

      * ('colname', 'element', bindings) -- for relations
          Creates a element named 'colname' bound to 'colname' column. The bindings
          represents the structure for the subelements.

    On shallow serializations, relations are represented by their ID, unless specified using the 3 element tuple form.

    One2Many relations are serialized as a list of the form
        <colname>
            <item>data</item>
            <item>data</item>
        </colname>
    where 'data' is either the ID or a XML fragment (if deep serialization)

    The return object is an lxml (http://codespeak.net/lxml) root element that can be further manipulated. You can
    generate a XML string with etree.tostring(root), where root is the output of this function.
    """

    columns = []
    for rule in bindings:
        # get the binding column
        if type(rule) == tuple:
            columns.append(rule[0])
        else:
            columns.append(rule)

    # Build data set
    datas = obj.read(cr, uid, ids, columns, context=context)

    # Build translation data
    if context is None:
        context = {}
    lang_obj = obj.pool.get('res.lang')
    fields = obj.fields_get(cr, uid)
    translatable = [k for k, v in fields.iteritems()
        if 'translate' in v and v['translate']]
    binding_fields = [rule if isinstance(rule, basestring) else rule[0]
        for rule in bindings]
    translatable = list(set(translatable).intersection(set(binding_fields)))
    if translatable:
        lang_ids = lang_obj.search(cr, uid, [('translatable', '=', True)])
        lang_codes = [v['code']
            for v in lang_obj.read(cr, uid, lang_ids, ['code'])
            if v['code'] != 'en_US']
        lang_datas = {}
        for lang in lang_codes:
            d = context.copy()
            d.update({'lang': lang})
            lang_datas[lang] = obj.read(cr, uid, ids, translatable, context=d)

    res = []
    for i, data in enumerate(datas):
        # create document
        root = etree.Element(unicode(root_tag))

        # do the binding for each binding rule
        for rule in bindings:
            # get the binding column
            col = rule if isinstance(rule, basestring) else rule[0]

            # get the element name
            if type(rule) == tuple and len(rule) > 1:
                ename = rule[1]
            else:
                ename = col

            # get the subcol if necessary
            if type(rule) == tuple and len(rule) > 2 and type(rule[2]) == str:
                subcol = rule[2]
            else:
                subcol = None

            # get the bindings for deep serialization
            if type(rule) == tuple and len(rule) > 2 and type(rule[2]) == list:
                deep_bindings = rule[2]
            else:
                deep_bindings = None

            # Create the element
            e = etree.SubElement(root, unicode(ename))

            # Append the value to the xml element
            def append(elem, value):

                if deep_bindings:
                    if value:
                        # seek relation object (very specific to OpenObject's ORM)
                        rel_obj_name = obj.fields_get(cr, uid, [col])[col]['relation']
                        rel_obj = obj.pool.get(rel_obj_name)

                        # get xml fragment from recursion
                        frag_root = obj_to_xml(rel_obj, cr, uid, [value], 'root', deep_bindings)[0]

                        # append children
                        for el in frag_root:
                            elem.append(el)

                elif subcol:
                    if value:
                        # seek relation object (very specific to OpenObject's ORM)
                        rel_field = obj.fields_get(cr, uid, [col])[col]
                        rel_obj_name = rel_field['relation']
                        rel_obj = obj.pool.get(rel_obj_name)

                        # query for value
                        sub_value = rel_obj.read(cr, uid, [value], [subcol])[0][subcol]
                        elem.text = unicode(sub_value)

                else:
                    # OpenObject return False if the relation is not defined.
                    # we should print False only if a boolean field. Else
                    # print nothing
                    if value or obj.fields_get(cr, uid, [col])[col]['type'] == 'boolean':
                        elem.text = unicode(value)
                        if col in translatable:
                            for lang in lang_datas:
                                elem.set(lang, lang_datas[lang][i][col])

            # Parse according to data return type
            if type(data[col]) == list:
                for _id in data[col]:
                    e_item = etree.SubElement(e,u'item')
                    append(e_item, _id)

            elif type(data[col]) == tuple:
                append(e, data[col][0])

            else:
                append(e, data[col])

        res.append(root)
    return res

def xml_to_vals(obj, cr, uid, xml, bindings, _type=None, idfield='global_id', recursion=False):
    """
    Returns a tuple according to OpenERP's expected format to be supplied in 'vals' argument in
    'create' and 'write' methods.

    The 'bindings' parameter is expected to be in the same format used for serialization in 'obj_to_xml'.

    The tuple returned is in the following format according to the specification in osv.fields.many2many:

         Values: (0, 0,  { fields })    create
                 (1, ID, { fields })    update
                 (2, ID)                remove
                 (6, ?, ids)            set a list of links

    """

    if type(xml) == str or type(xml) == unicode:
        xml = objectify.fromstring(xml)
    if xml.tag == 'message':
        _type = xml.get('type')
        xml = xml.iterchildren().next()

    #Translation handling
    lang_data = {False: {}}
    lang_codes = []
    if not recursion:
        lang_obj = obj.pool.get('res.lang')
    #    fields = obj.fields_get(cr, uid)
    #    translatable = [k for k, v in fields.iteritems() if 'translate' in v and v['translate']]
        lang_ids = lang_obj.search(cr, uid, [('translatable', '=', True)])
        lang_codes = [v['code'] for v in lang_obj.read(cr, uid, lang_ids, ['code']) if v['code'] != 'en_US']
        for lang in lang_codes:
            lang_data[lang] = {}

    data = dict()
    deep_cols = []
    # do the binding for each binding rule
    for rule in bindings:
        try:
            # get the binding column
            if type(rule) == tuple:
                col = rule[0]
            else:
                col = rule


            # get the element name
            if type(rule) == tuple and len(rule) > 1:
                ename = rule[1]
            else:
                ename = col


            # get the subcol if necessary
            if type(rule) == tuple and len(rule) > 2 and type(rule[2]) == str:
                subcol = rule[2]
            else:
                subcol = None

            # get the bindings for deep serialization
            if type(rule) == tuple and len(rule) > 2 and type(rule[2]) == list:
                deep_bindings = rule[2]
                deep_cols.append(col)
            else:
                deep_bindings = None

            # seek field object (very specific to OpenObject's ORM)
            if col == 'id':
                field = {'type': None}
            else:
                field = obj.fields_get(cr, uid, [col])[col]
                if 'relation' in field:
                    field_obj = obj.pool.get(field['relation'])


            # Expect a string value
            # or a xml fragment
            def append(value, dest=data):
                if deep_bindings:
                    if len(value):

                        # get the tuple from recursion and append
                        frag_tupl = xml_to_vals(field_obj, cr, uid, value, deep_bindings, _type, recursion=True)
                        dest[col].append(frag_tupl)


                else:
                    if subcol:
                        if len(value):
                            # query for id.
                            res = field_obj.search(cr, uid, [(subcol, '=', str(value))], context={'active_test': False})
                            assert len(res) > 0, 'Value "%s" not found in column "%s" for object %s' % (value, subcol, field['relation'])
                            assert len(res) == 1, 'More then one value "%s" found in column "%s" for object %s' % (value, subcol, field['relation'])
                            value = res[0]


                    if field['type'] in ('boolean', 'integer', 'integer_big', 'float'):
                        if len(value):
                            dest[col] = eval(str(value))
                        else:
                            dest[col] = False

                    elif field['type'] in ('one2many', 'many2many'):
                        if len(value):
                            dest[col][0][2].append(value)

                    elif field['type'] in ('many2one', ):
                        if len(value):
                            dest[col] = int(str(value))

                    else:
                        if len(value):
                            dest[col] = unicode(value)


            if field['type'] in ('one2many', 'many2many'):
                if deep_bindings:
                    data[col] = []
                else:
                    data[col] = [(6,0,[])]

                for e in getattr(xml, ename).iterchildren():
                    append(e)
            else:
                try:
                    append(getattr(xml, ename))
                    #Translation handling
                    for lang in lang_codes:
                        if lang in getattr(xml, ename).keys():
                            append(getattr(xml, ename).get(lang), lang_data[lang])
                except AttributeError:
                    data[col] = None

        except Exception, e:
            log.exception(e)
            raise DeserializationError(str(rule), e)

    #Translation handling
    lang_data[False] = data

    if _type in ['create', 'update']:

        # Get the ID of the object
        # Expects either an ID or a global ID
        if 'id' in data:
            obj_id = int(data['id'])
            data.pop('id')
            tup = (1, obj_id, lang_data[False] if recursion else lang_data)
        else:
            # Try to find an object with the same global ID
            if idfield in data:
                res = obj.search(cr, uid, [(idfield, '=', data[idfield])], context={'active_test': False})
                if res:
                    _id = int(res[0])
                    tup = (1, _id, lang_data[False] if recursion else lang_data) # update if found
                else:
                    return (0, 0, lang_data[False] if recursion else lang_data) # create a new one if not
            else:
                return (0, 0, lang_data[False] if recursion else lang_data) # create a new one if not

        # Unlink child objects if not referenced in xml
        for col in deep_cols:
            field = obj.fields_get(cr, uid, [col])[col]
            xml_ids = set([x[1] for x in data[col]])
            all_ids = set(obj.read(cr, uid, [tup[1]], [col])[0][col])
            surplus_ids = all_ids - xml_ids
            for x in surplus_ids:
                data[col].append((2,x,{}))

        return tup

    else:
        raise Exception('Operation "%s" not implemented' % _type)


# Add to osv.osv
osv.osv.obj_to_xml = obj_to_xml
osv.osv.xml_to_vals = xml_to_vals

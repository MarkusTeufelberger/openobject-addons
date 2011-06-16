# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Fixes, improvements and V6 adaptation by Guewen Baconnier - Camptocamp 2011

from osv import fields, osv
from tools.translate import _
import tools


class base_partner_merge(osv.osv_memory):
    '''
    Merges two partners
    '''
    _name = 'base.partner.merge'
    _description = 'Merges two partners'

    _columns = {
    }
    
    _values = {}

    def _build_form(self, cr, uid, field_datas, value1, value2):
        formxml = '''<?xml version="1.0"?>
            <form string="%s">
            <separator colspan="4" string="Select datas for new record"/>''' % _('Merge')
        update_values = {}
        update_fields = {}
        columns = {}

        for fid, fname, fdescription, ttype, required, relation, readonly in field_datas:
            val1 = value1[fname]
            val2 = value2[fname]
            my_selection = []
            size = 24

            if (val1 and val2) and (val1 == val2):
                if ttype in ('many2one'):
                    update_values.update({fname: val1.id})
                elif ttype in ('many2many'):
                    update_values.update({fname: [(6, 0, map(lambda x: x.id, val1))]})
                else:
                    update_values.update({fname: val1})

            if (val1 and val2) and (val1 != val2) and not readonly:
                if ttype in ('char', 'text', 'selection'):
                    my_selection = [(val1, val1), (val2, val2)]
                    size = max(len(val1), len(val2))
                if ttype in ('float', 'integer'):
                    my_selection = [(str(val1), str(val1)), (str(val2), str(val2))]
                if ttype in ('many2one'):
                    my_selection = [(str(val1.id), val1.name),
                                    (str(val2.id), val2.name)]
                if ttype in ('many2many'):
                    update_values.update({fname: [(6, 0, list(set(map(lambda x: x.id, val1 + val2))))]})
                if my_selection:
                    if not required:
                        my_selection.append((False, ''))
                    columns.update({fname: fields.selection(my_selection, fdescription, required=required, size=size)})
                    update_fields.update({fname: {'string': fdescription, 'type': 'selection', 'selection': my_selection, 'required': required}})
                    formxml += '\n<field name="%s"/><newline/>' % (fname,)
            if (val1 and not val2) or (not val1 and val2):
                if ttype == 'many2one':
                    update_values.update({fname: val1 and val1.id or val2 and val2.id})
                elif ttype == 'many2many':
                    update_values.update({fname: [(6, 0, map(lambda x: x.id, val1 or val2))]})
                elif ttype == 'one2many':
                    #skip one2many values
                    pass
                else:
                    update_values.update({fname: val1 or val2})

        formxml += """
        <separator colspan="4"/>
        <group col="4" colspan="4">
            <label string="" colspan="2"/>
            <button special="cancel" string="Cancel" icon="gtk-cancel"/>
            <button name="action_merge" string="Merge" type="object" icon="gtk-ok"/>
        </group>
        </form>"""
        return formxml, update_fields, update_values, columns

    def check_partners(self, cr, uid, partner_ids, context):
        """ Check validity of selected addresses.
         Hook for other checks
        """
        if not len(partner_ids) == 2:
            raise osv.except_osv(_('Error!'), _('You must select only two partners'))
        return True

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(base_partner_merge, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        partner_ids = context.get('active_ids') or []

        self.check_partners(cr, uid, partner_ids, context)

        if not len(partner_ids) == 2:
            return res
        partner_obj = self.pool.get('res.partner')
        cr.execute("SELECT id, name, field_description, ttype, required, relation, readonly from ir_model_fields where model='res.partner'")
        field_datas = cr.fetchall()
        partner1 = partner_obj.browse(cr, uid, partner_ids[0], context=context)
        partner2 = partner_obj.browse(cr, uid, partner_ids[1], context=context)
        myxml, merge_fields, self._values, columns = self._build_form(cr, uid, field_datas, partner1, partner2)
        self._columns.update(columns)
        res['arch'] = myxml
        res['fields'] = merge_fields
        return res

    def cast_many2one_fields(self, cr, uid, data_record, context=None):
        """ Some fields are many2one and the ORM expect them to be integer or in the form
        'relation,1' wher id is the id.
         As some fields are displayed as selection in the view, we cast them in integer.
        """
        cr.execute("SELECT name from ir_model_fields where model='res.partner' and ttype='many2one'")
        fields = cr.fetchall()
        for field in fields:
            if data_record.get(field[0], False):
                data_record[field[0]] = int(data_record[field[0]])
        return data_record

    def action_merge(self, cr, uid, ids, context=None):
        """
        Merges two partners and create 3rd and changes references of old partners with new
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: id of the wizard
        @param context: A standard dictionary for contextual values

        @return : nothing
        """
        record_id = context and context.get('active_id', False) or False
        pool = self.pool
        if not record_id:
            return {}
        res = self.read(cr, uid, ids, context = context)[0]

        res.update(self._values)
        partner_pool = pool.get('res.partner')
        partner_ids = context.get('active_ids') or []
        if not len(partner_ids) == 2:
            raise osv.except_osv(_('Error!'), _('You must select only two partners'))

        self.check_partners(cr, uid, partner_ids, context)

        part1 = partner_ids[0]
        part2 = partner_ids[1]

        if hasattr(partner_pool, '_sql_constraints'):
            #for uniqueness constraint (vat number for example)...
            c_names = []
            remove_field = {}
            unique_fields = []
            for const in partner_pool._sql_constraints:
                c_names.append('res_partner_' + const[0])
            if c_names:
                c_names = tuple(map(lambda x: "'"+ x +"'", c_names))
                cr.execute("""select column_name from \
                        information_schema.constraint_column_usage u \
                        join  pg_constraint p on (p.conname=u.constraint_name) \
                        where u.constraint_name in (%s) and p.contype='u' """ % c_names)
                for i in cr.fetchall():
                    remove_field[i[0]] = None
                    unique_fields.append(i[0])
                    unique_fields.append('name')
                    unique_data = partner_pool.read(cr, uid, [part1, part2], unique_fields)
                    str_unq = '---------------------------------------\n'
                    for u in unique_data:
                        for key, value in u.items():
                            if key == 'id' or not value:
                                continue
                        str_unq += key + ': ' + str(value) + '\n'
                    if res.has_key('comment') and res['comment']:
                        res['comment'] += '\n' + str_unq
                    else:
                        res['comment'] = str_unq
        list_partn = []
        list_partn.append(part1)
        list_partn.append(part2)
        count_default_address = 0
        for partner in partner_pool.browse(cr, uid, list_partn):
            for address in partner.address:
                if address.type == 'default':
                    count_default_address +=1
        if count_default_address > 1:
            raise osv.except_osv(_('Error!'), _('You have more than one default type in your addresses.\n Please change it and test once again!'))


        remove_field.update({'active': False})
        try:
            partner_pool.write(cr, uid, [part1, part2], remove_field, context=context)
        except:
            raise osv.except_osv(_('Error!'), _('You have to change the type of the default address of one of the partner to avoid having two default addresses'))

        res = self.cast_many2one_fields(cr, uid, res, context)

        part_id = partner_pool.create(cr, uid, res, context=context)

        self.custom_updates(cr, uid, part_id, [part1, part2], context)

        # For one2many fields on res.partner
        cr.execute("select name, model from ir_model_fields where relation='res.partner' and ttype not in ('many2many', 'one2many');")
        for name, model_raw in cr.fetchall():
            if hasattr(pool.get(model_raw), '_auto'):
                if not pool.get(model_raw)._auto:
                    continue
            elif hasattr(pool.get(model_raw), '_check_time'):
                continue
            else:
                if hasattr(pool.get(model_raw), '_columns'):
                    from osv import fields
                    if pool.get(model_raw)._columns.get(name, False) and isinstance(pool.get(model_raw)._columns[name], fields.many2one):
                        model = model_raw.replace('.', '_')
                        if name not in ('relation_partner_answer'):
                            cr.execute("update "+model+" set "+name+"="+str(part_id)+" where "+ tools.ustr(name) +" in ("+ tools.ustr(part1) +", "+tools.ustr(part2)+")")

        return {}

    def custom_updates(self, cr, uid, partner_id, old_partner_ids, context):
        """Hook for special updates on old partners and new partner
        """
        pass

base_partner_merge()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


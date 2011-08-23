# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    This module is copyright (C) 2011 Numérigraphe SARL. All Rights Reserved.
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

import wizard
import tools
import pooler
import netsvc
from osv import fields,osv
from tools.translate import _

class wizard_copy_translations(osv.osv_memory):

    def _get_languages(self, cr, uid, context):
        lang_obj = pooler.get_pool(cr.dbname).get('res.lang')
        ids = lang_obj.search(cr, uid, ['&', ('active', '=', True), ('code', '<>', 'en_US'), ('translatable', '=', True),])
        langs = lang_obj.browse(cr, uid, ids)
        return [(lang.code, lang.name) for lang in langs]
    
    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def act_copy(self, cr, uid, ids, context=None):
        """
        Copy the translations from a language to en_US.
        
        When object model fields are translatable, only the English version is
        stored in the database table.
        The translations into other languages are stored as
        ir_translation object resources.
        This method will copy a translation to the English version in every
        object."""
        
        logger = netsvc.Logger()
        this = self.browse(cr, uid, ids)[0]
        trans_obj = pooler.get_pool(cr.dbname).get('ir.translation')
        logger.notifyChannel("wizard_copy_translations",
            netsvc.LOG_DEBUG,
            "Copying translations from %s to en_US" % this.lang)
        # Read all the model translations in the new language
        trans_ids = trans_obj.search(cr, uid, [
             ('type', '=', 'model'),
             ('lang', '=', this.lang),
             ('value', '!=', ''),
            ], context=None)
        translations = trans_obj.browse(cr, uid, trans_ids, context=None)
        for trans in translations:
            # Get the object and field name
            (model, field) = trans.name.split(',', 1)
            # Read the English version from the object
            object = pooler.get_pool(cr.dbname).get(model)
            value = object.read(cr, uid, trans.res_id, fields=[field],
                context=None)
            if value and value[field] != trans.value:
                logger.notifyChannel("wizard_copy_translations",
                    netsvc.LOG_DEBUG,
                    "Changing %s in %s id %d from %s to %s" % (
                        field, model, trans.res_id, value[field], trans.value))
                # Copy the versions in the new language to the English version
                # We could pass trans.res_id as a single integer,
                # but some buggy objects would break
                object.write(cr, uid, [trans.res_id], {field: trans.value},
                    context=None)
        logger.notifyChannel("wizard_copy_translations",
            netsvc.LOG_DEBUG, "Done")
        return self.write(cr, uid, ids, {'state':'done'}, context=context)

    _name = "wizard.translation.copy"
    _columns = {
            'lang': fields.selection(_get_languages, 'Language', help='All the strings in English will be overwritten with the translations from language.'),
            'state': fields.selection( ( ('choose','choose'),   # choose language
                                         ('done','done'),       # Copy done
                                       ) ),
            }
    _defaults = {
            'state': lambda *a: 'choose'
                }
wizard_copy_translations()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


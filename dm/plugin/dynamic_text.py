# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import pooler

__description__ = """This plugin return a text based on the languge selected 
                    in the document and gender from workitem's partner gender"""

def dynamic_text(cr, uid, **args):
    doc_id = args['document_id']
    pool = pooler.get_pool(cr.dbname)
    doc_obj = pool.get('dm.offer.document').browse(cr, uid, doc_id)
    lang_id = doc_obj.lang_id.id
    title_obj = pool.get('res.partner.title')
    if args['doc_type'] == 'preview':
        address_id = pool.get('res.partner.address').browse(cr, uid, 
                                                        args['address_id'])
    else:
        workitem_id = pool.get('dm.workitem').browse(cr, uid, 
                                                     args['workitem_id'])
        address_id = workitem_id.address_id
    title_srch_id = title_obj.search(cr, uid, 
                    [('shortcut', '=', address_id.title)])
    if not title_srch_id:
        return False
    gender_id = title_obj.browse(cr, uid, title_srch_id[0]).gender_id.id
    criteria = [('language_id', '=', lang_id),('gender_id', '=', gender_id),
                                    ('ref_text_id', '=', args['ref_text_id'])]
    if 'previous_step_id' in args:
        criteria.append(('previous_step_id', '=', args['previous_step_id']))
    dynamic_text_id = pool.get('dm.dynamic_text').search(cr, uid, criteria)
    if dynamic_text_id:
        dynamic_text = pool.get('dm.dynamic_text').read(cr, uid, 
                                    dynamic_text_id[0], ['content'])['content']
        return dynamic_text
    return ""


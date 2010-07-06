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

import wizard
import pooler

segment_form = """<?xml version="1.0" ?>
<form string="Duplication Of Campaign">
    <field name="keep_segments"/>
</form>"""

segment_fields = {
    'keep_segments':{'string': 'Keep Segments At Duplication', 
                     'type': 'boolean', 'default': lambda *a: True},
}

def _copy_segment(self, cr, uid, data, context):
    prop_id = data['id']
    seg = data['form']['keep_segments']
    pool = pooler.get_pool(cr.dbname)
    prp_id = pool.get('dm.campaign').copy(cr, uid, prop_id) 
    datas = pool.get('dm.campaign').browse(cr, uid, prp_id, context)
    if datas.proposition_ids:
        if not seg:
            for j in datas.proposition_ids:
                dd = j.id
                camp_prop = pool.get('dm.campaign.proposition').browse(cr, uid, dd)
                l = []
                for i in camp_prop.segment_ids:
                    l.append(i.id)
                    pool.get('dm.campaign.proposition.segment').unlink(cr, uid, l)
            return {'PRP_ID': prp_id}
    return {'PRP_ID': prp_id}

class wizard_campaign_copy(wizard.interface):
    states = {
        'init':{
            'actions': [],
            'result': {'type': 'form', 'arch': segment_form, 
                       'fields': segment_fields, 
                       'state': [('end', 'Cancel'), ('copy', 'Duplicate')]},
        },
        'copy': {
            'actions': [],
            'result': {'type': 'action', 'action': _copy_segment, 
                       'state': 'end'}
        }
    }
wizard_campaign_copy("wizard_campaign_copy")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
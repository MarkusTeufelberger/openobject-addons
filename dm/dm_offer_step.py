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

import netsvc

from osv import fields
from osv import osv

AVAILABLE_STATES = [
    ('draft', 'Draft'),
    ('open', 'Open'),
    ('freeze', 'Freeze'),
    ('closed', 'Close')
]

AVAILABLE_ITEM_TYPES = [
    ('main', 'Main Item'),
    ('standart', 'Standart Item'),
]

class dm_offer_step_type(osv.osv): # {{{
    _name = "dm.offer.step.type"
    _rec_name = 'name'

    _columns = {
        'name': fields.char('Name', size=64, translate=True, required=True),
        'code': fields.char('Code', size=8, translate=True, required=True),
        'flow_start': fields.boolean('Flow Start'),
        'flow_stop': fields.boolean('Flow Stop'),
        'description': fields.text('Description', translate=True),
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
    ]

dm_offer_step_type() # }}}

class dm_offer_step(osv.osv): # {{{
    _name = "dm.offer.step"

    _columns = {
        'seq': fields.integer('Sequence'),
        'name': fields.char('Name', size=64, required=True, 
                                       states={'closed': [('readonly', True)]}),
        'offer_id': fields.many2one('dm.offer', 'Offer', required=True, 
                    ondelete="cascade", states={'closed': [('readonly',True)]}),
        'parent_id': fields.many2one('dm.offer', 'Parent'),
        'legal_state': fields.char('Legal State', size=32, 
                                      states={'closed': [('readonly', True)]}),
        'code': fields.char('Code', size=64, required=True, translate=True),
        'quotation': fields.char('Quotation', size=16, 
                                    states={'closed': [('readonly', True)]}),
        'media_id': fields.many2one('dm.media', 'Media', ondelete="cascade",
                        required=True, states={'closed': [('readonly', True)]}),
        'type_id': fields.many2one('dm.offer.step.type', 'Type', required=True, 
                                   states={'closed': [('readonly', True)]}),
        'origin_id': fields.many2one('dm.offer.step', 'Origin'),
        'desc': fields.text('Description', 
                                    states={'closed': [('readonly', True)]}),
        'dtp_note': fields.text('DTP Notes', 
                                    states={'closed': [('readonly', True)]}),
        'dtp_category_ids': fields.many2many('dm.offer.category', 
                                        'dm_offer_dtp_category', 'offer_id',
                                        'offer_dtp_categ_id', 'DTP Categories'),
        'trademark_note': fields.text('Trademark Notes', 
                                      states={'closed': [('readonly', True)]}),
        'trademark_category_ids': fields.many2many('dm.offer.category',
                            'dm_offer_trademark_category', 'offer_id',
                            'offer_trademark_categ_id', 'Trademark Categories'),
        'production_note': fields.text('Production Notes', 
                                       states={'closed': [('readonly', True)]}),
        'planning_note': fields.text('Planning Notes', 
                                     states={'closed': [('readonly', True)]}),
        'purchase_note': fields.text('Purchase Notes', 
                                     states={'closed': [('readonly', True)]}),
        'mailing_at_dates': fields.boolean('Mailing at dates', 
                                    states={'closed': [('readonly', True)]}),
        'floating_date': fields.boolean('Floating date', 
                                    states={'closed': [('readonly', True)]}),
        'interactive': fields.boolean('Interactive', 
                                    states={'closed': [('readonly', True)]}),
        'notes': fields.text('Notes'),
        'document_ids': fields.one2many('dm.offer.document', 
                                            'step_id', 'DTP Documents'),
        'flow_start': fields.boolean('Flow Start'),
        'state': fields.selection(AVAILABLE_STATES, 'Status', 
                                            size=16, readonly=True),
        'incoming_transition_ids': fields.one2many('dm.offer.step.transition',
                            'step_to_id', 'Incoming Transition', readonly=True),
        'outgoing_transition_ids': fields.one2many('dm.offer.step.transition',
                                    'step_from_id', 'Outgoing Transition', 
                                    states={'closed': [('readonly', True)]}),
        'split_mode': fields.selection([('and', 'And'),('or', 'Or'),
                                                ('xor', 'Xor')], 'Split mode'),
        'doc_number': fields.integer('Number of documents of the mailing', 
                                     states={'closed': [('readonly', True)]}),
        'action_id': fields.many2one('ir.actions.server', 
                                            string='Action', required=True),
        'graph_hide': fields.boolean('Hide in Offer Graph'),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'split_mode': lambda *a: 'or',
    }

    def onchange_code(self,cr,uid,ids,type_id,context):
        step_type = self.pool.get('dm.offer.step.type').browse(cr, 
                                                            uid, [type_id])[0]
        res_code = self.pool.get('ir.translation')._get_ids(cr, uid, 
                        'dm.offer.step.type,code', 'model', 
                        context.get('lang', False) or 'en_US', [step_type.id])
        type_code = res_code[step_type.id] or step_type.code
        value = {
                 'code': type_code
                }
        return {'value': value}

    def onchange_type(self, cr, uid, ids, type_id, offer_id, context):
        step_type = self.pool.get('dm.offer.step.type').browse(cr, 
                                                            uid, [type_id])[0]
        value = {
                    'flow_start': step_type['flow_start'],
                }
        if offer_id:
            offer = self.pool.get('dm.offer').browse(cr, uid, [offer_id])[0]
            if offer.type == 'model':
                res_trans = self.pool.get('ir.translation')._get_ids(cr, uid, 
                        'dm.offer.step.type,name', 'model', 
                        context.get('lang', False) or 'en_US', [step_type.id])
                type_code = res_trans[step_type.id] or step_type.name
                value['name'] = step_type.name
            else:
                res_code = self.pool.get('ir.translation')._get_ids(cr, uid, 
                        'dm.offer.step.type,code', 'model', 
                        context.get('lang', False) or 'en_US', [step_type.id])
                type_code = res_code[step_type.id] or step_type.code
#                res_offer = self.pool.get('ir.translation')._get_ids(cr, uid, 'dm.offer,name', 'model', context.get('lang', False) or 'en_US',[offer.id])
#                offer_name = res_offer[offer.id] or offer.name
                value['name'] = "%s for %s"% (type_code, offer.name) 
        return {'value': value}

    def create(self,cr,uid,vals,context={}):
        if 'type_id' in vals and vals['type_id']:
            type_seq = self.search(cr,uid,[('type_id','=',vals['type_id']),('offer_id','=',vals['offer_id'])])
            vals['seq'] = len(type_seq) and len(type_seq)+1 or 1
        return super(dm_offer_step,self).create(cr,uid,vals,context)

    def write(self,cr,uid,ids,vals,context={}):
        if 'type_id' in vals and vals['type_id']:
            step  = self.browse(cr,uid,ids)[0]
            if vals['type_id'] != step.type_id.id:
                type_seq = self.search(cr, uid, 
                                        [('type_id', '=', vals['type_id']), 
                                         ('offer_id', '=', step.offer_id.id)])
                vals['seq'] = len(type_seq) and len(type_seq)+1 or 1
        return super(dm_offer_step, self).write(cr, uid, ids, vals, context)


    def state_close_set(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'closed'})
        return True

    def state_open_set(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for step in self.browse(cr, uid, ids, context):
            for doc in step.document_ids:
                if doc.state != 'validate':
                    raise osv.except_osv(
                            _('Could not open this offer step !'),
                            _('You must first validate all documents \
                                                attached to this offer step.'))
            wf_service.trg_validate(uid, 'dm.offer.step', step.id, 'open', cr)
        self.write(cr, uid, ids, {'state': 'open'})
        return True

    def state_freeze_set(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'freeze'})
        return True

    def state_draft_set(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True
    
    def search(self, cr, uid, args, offset=0, limit=None, 
                        order=None, context=None, count=False):
        if context and 'dm_camp_id' in context:
            if not context['dm_camp_id']:
                return []
            res  = self.pool.get('dm.campaign').browse(cr, uid, context['dm_camp_id'])
            step_ids = map(lambda x: x.id, res.offer_id.step_ids)
            return step_ids
        return super(dm_offer_step, self).search(cr, uid, args, offset, 
                                                 limit, order, context, count)


dm_offer_step() # }}}

class dm_offer_step_transition_trigger(osv.osv): # {{{
    _name = "dm.offer.step.transition.trigger"
    _rec_name = "name"
    _columns = {
        'name': fields.char('Trigger Name', size=64, 
                                    required=True, translate=True),
        'code': fields.char('Code', size=64, required=True, translate=True),
        'gen_next_wi': fields.boolean('Auto Generate Next Workitems'),
        'in_act_cond': fields.text('Action Condition', required=True),
#        'out_act_cond': fields.text('Outgoing Action Condition', required=True),
        'type': fields.selection([('offer', 'Offer'), ('as', 'After-Sale')],
                                        'Type', required=True),
    }
    _defaults = {
        'gen_next_wi': lambda *a: 'False',
        'in_act_cond': lambda *a: 'result = False',
        'type': lambda *a: 'offer',
#        'out_act_cond': lambda *a: 'result = False',
    }
dm_offer_step_transition_trigger() # }}}

class dm_offer_step_transition(osv.osv): # {{{
    _name = "dm.offer.step.transition"
#    _rec_name = 'condition_id'
    _rec_name = 'step_from_id'
    _columns = {
        'condition_id': fields.many2one('dm.offer.step.transition.trigger', 
                        'Trigger Condition', required=True, ondelete="cascade"),
        'delay': fields.integer('Action Delay', required=True),
        'action_hour': fields.float('Action Hour'),
        'action_day': fields.integer('Action Month Day'),
        'action_date': fields.datetime('Action Date'),
#        'action_week_day': fields.selection([('0', 'Monday'),('1', 'Tuesday'),
#                         '2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'),
#                         ('5', 'Saturday'), ('6', 'Sunday')], 'Action Day'),
        'delay_type': fields.selection([('minute', 'Minutes'),('hour', 'Hours'),
                            ('day', 'Days'), ('week', 'Weeks'), 
                            ('month', 'Months')], 'Delay type', required=True),
        'step_from_id': fields.many2one('dm.offer.step', 'From Offer Step',
                                            required=True, ondelete="cascade"),
        'step_to_id': fields.many2one('dm.offer.step', 'To Offer Step',
                                            required=True, ondelete="cascade"),
        'graph_hide': fields.boolean('Hide in Offer Graph'),
    }
    _defaults = {
        'delay_type': lambda *a: 'day',
    }
    def default_get(self, cr, uid, fields, context={}):
        data = super(dm_offer_step_transition, self).default_get(cr, uid, fields, context)
        if context.has_key('type_id'):
            data['delay'] = '0'
            data[context['type_id']] = context['step_id']
        return data

dm_offer_step_transition() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


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
from tools.translate import _

AVAILABLE_STATES = [ # {{{
    ('draft', 'Draft'),
    ('ready', 'Ready To Plan'),
    ('open', 'Open'),
    ('freeze', 'Freeze'),
    ('closed', 'Close'),
] # }}}

AVAILABLE_TYPE = [ # {{{
    ('model', 'Model'),
    ('new', 'New'),
    ('standart', 'Standart'),
    ('rewrite', 'Rewrite'),
    ('preoffer', 'Offer Idea'),
    ('as', 'After-Sale')
] # }}}:w


class dm_media(osv.osv): # {{{
    _name = "dm.media"
    """
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if 'step_media_ids' in context and context['step_media_ids']:
            if context['step_media_ids'][0][2]:
                brse_rec = context['step_media_ids'][0][2]
            else:
                raise osv.except_osv('Error !', "It is necessary to select media in offer step.")
        else:
            brse_rec = super(dm_media, self).search(cr, uid, [])
        return brse_rec
    """
    _columns = {
        'name': fields.char('Name', size=64, translate=True, required=True),
        'code': fields.char('Code', size=64, translate=True, required=True),
    }
dm_media() # }}}


class dm_trademark(osv.osv):
    _name = "dm.trademark"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=6, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', required=False),
        'header': fields.binary('Header (.odt)'),
        'logo': fields.binary('Logo'),
        'logo_url': fields.char('URL', size=128),
        'signature': fields.binary('Signature'),
        'signature_url': fields.char('URL', size=128),
        'banner_top': fields.binary('Top Banner'),
        'banner_top_url': fields.char('URL', size=128),
        'banner_bottom': fields.binary('Bottom Banner'),
        'banner_bottom_url': fields.char('URL', size=128),
        'media_id': fields.many2one('dm.media', 'Media'),
        'email': fields.char('Email', size=64),
        'website': fields.char('Website', size=64),
    }

dm_trademark() # }}}


class dm_offer_category(osv.osv): # {{{
    _name = "dm.offer.category"
    _rec_name = "name"

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name', 'parent_id'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1] + ' / ' + name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = self.name_get(cr, uid, ids)
        return dict(res)

    def _check_recursion(self, cr, uid, ids):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from dm_offer_category \
                                where id in ('+', '.join(map(str, ids))+')')
            ids = filter(None, map(lambda x: x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _columns = {
        'complete_name': fields.function(_name_get_fnc, method=True,
                                         type='char', string='Category'),
        'parent_id': fields.many2one('dm.offer.category', 'Parent'),
        'name': fields.char('Name', size=64, required=True),
        'child_ids': fields.one2many('dm.offer.category', 'parent_id',
                                                            'Childs Category'),
    }

    _constraints = [
        (_check_recursion, 'Error ! You can not create recursive categories.',
                                                                 ['parent_id'])
    ]

dm_offer_category() # }}}


class dm_offer_production_cost(osv.osv): # {{{
    _name = "dm.offer.production.cost"
    _columns = {
        'name': fields.char('Name', size=32, required=True)
    }

dm_offer_production_cost() # }}}

class dm_offer(osv.osv): # {{{
    _name = "dm.offer"
    _rec_name = 'name'

    def dtp_last_modification_date(self, cr, uid, ids, field_name, arg,
                                                                    context={}):
        result = {}
        for id in ids:
            sql = "select write_date, create_date from dm_offer where id = %s"
            cr.execute(sql, [id])
            res = cr.fetchone()
            if res[0]:
                result[id] = res[0].split(' ')[0]
            else:
                result[id] = res[1].split(' ')[0]
        return result

    def _check_preoffer(self, cr, uid, ids):
        offer = self.browse(cr, uid, ids)[0]
        if offer.preoffer_original_id:
            preoffer_id = self.search(cr, uid, [('preoffer_original_id', '=',
                                            offer.preoffer_original_id.id)])
            if len(preoffer_id) > 1:
                return False
        return True

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=16, required=True),
        'lang_orig_id': fields.many2one('res.lang', 'Original Language',
                                                                required=True),
        'copywriter_id': fields.many2one('res.partner', 'Copywriter',
                                domain=[('category_id', 'ilike', 'Copywriter')],
                                context={'category': 'Copywriter'}),
        'step_ids': fields.one2many('dm.offer.step', 'offer_id', 'Offer Steps'),
        'offer_responsible_id': fields.many2one('res.users', 'Responsible',
                                                            ondelete="cascade"),
        'recommended_trademark_id': fields.many2one('dm.trademark',
                                                    'Recommended Trademark'),
        'offer_origin_id': fields.many2one('dm.offer', 'Original Offer',
                                            domain=[('type', 'in',
                                              ['new', 'standart', 'rewrite'])]),
        'preoffer_original_id': fields.many2one('dm.offer',
                                'Original Offer Idea',
                                 domain = [('type', '=', 'preoffer')]),
        'active': fields.boolean('Active'),
        'quotation': fields.char('Quotation', size=16),
        'legal_state': fields.selection([('validated', 'Validated'),
                                         ('notvalidated', 'Not Validated'),
                                         ('inprogress', 'In Progress'),
                                         ('refused', 'Refused')],
                                         'Legal State'),
        'category_ids': fields.many2many('dm.offer.category',
                                        'dm_offer_category_rel',
                                        'offer_id',
                                        'offer_category_id',
                                        'Categories'),
        'notes': fields.text('General Notes'),
        'state': fields.selection(AVAILABLE_STATES, 'Status', size=16,
                                                            readonly=True),
        'type': fields.selection(AVAILABLE_TYPE, 'Type', size=16),
        'preoffer_offer_id': fields.many2one('dm.offer', 'Offer',
                                             domain=[('type', 'in',
                                                    ['new', 'standart',
                                                    'rewrite'])]),
        'preoffer_type': fields.selection([('rewrite', 'Rewrite'),
                                           ('new', 'New')],
                                           'Type', size=16),
        'production_category_ids': fields.many2many('dm.offer.category',
                                                'dm_offer_production_category',
                                                'offer_id',
                                                'offer_production_categ_id',
                                                'Production Categories',
                                      domain="[('domain', '=', 'production')]"),
        'production_cost_id': fields.many2one('dm.offer.production.cost',
                                              'Production Cost'),
        'purchase_note': fields.text('Purchase Notes'),
        'purchase_category_ids': fields.many2many('dm.offer.category',
                                                  'dm_offer_purchase_category',
                                                  'offer_id',
                                                  'offer_purchase_categ_id',
                                                  'Purchase Categories',
                                     domain="[('domain', '=', 'purchase')]"),
        'history_ids': fields.one2many('dm.offer.history', 'offer_id',
                                       'History', ondelete="cascade",
                                        readonly=True),

        'order_date': fields.date('Order Date'),
        'last_modification_date': fields.function(dtp_last_modification_date,
                                            method =True, type="char",
                                            string ='Last Modification Date',
                                            readonly =True),
        'planned_delivery_date': fields.date('Planned Delivery Date'),
        'delivery_date': fields.date('Delivery Date'),
        'fixed_date': fields.date('Fixed Date'),
        'forbidden_country_ids': fields.many2many('res.country',
                                            'dm_offer_forbidden_country',
                                            'offer_id', 'country_id',
                                            'Forbidden Countries'),
        'forbidden_state_ids': fields.many2many('res.country.state',
                                                'dm_offer_forbidden_state',
                                                'offer_id', 'state_id',
                                                'Forbidden States'),
        'keywords': fields.text('Keywords'),
        'version': fields.char('Version', size=64),
        'child_ids': fields.one2many('dm.offer', 'offer_origin_id',
                                                           'Childs Category'),
    }

    _defaults = {
        'active': lambda *a: 1,
        'state': lambda *a: 'draft',
        'type': lambda *a: 'new',
        'preoffer_type': lambda *a: 'new',
        'legal_state': lambda *a: 'validated',
        'offer_responsible_id': lambda obj, cr, uid, context: uid,
    }

    _constraints = [
        (_check_preoffer, 'Error ! this offer idea is already assigned \
                                  to an offer', ['preoffer_original_id'])
    ]

    def state_close_set(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService('workflow')
        for step in self.browse(cr, uid, ids):
            wf_service.trg_validate(uid, 'dm.offer.step',
                                            step.id, 'state_close_set',  cr)
        self.write(cr, uid, ids, {'state': 'closed'})
        return True

    def state_ready_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'ready'})
        return True

    def state_open_set(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService("workflow")
        for step in self.browse(cr, uid, ids):
            for step_id in step.step_ids:
                if step_id.state != 'open':
                    raise osv.except_osv(_('Could not open this offer !'), _('You must first open all offer steps related to this offer.'))
            wf_service.trg_validate(uid, 'dm.offer', step.id, 'open', cr)
        self.write(cr, uid, ids, {'state': 'open'})
        return True

    def state_freeze_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'freeze'})
        return True

    def state_draft_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for off_id in ids:
            wf_service.trg_create(uid, 'dm.offer', off_id, cr)
        return True

    def go_to_offer(self, cr, uid, ids, *args):
        self.copy(cr, uid, ids[0], {'type': 'standart'})
        return True

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False,) : # submenu=False): for trunk client
        if 'offer_type' in context and context['offer_type']:
            new_view_id = self.pool.get('ir.ui.view').search(cr, user,
                                           [('name', '=', 'dm.preoffer.form')])
            result = super(dm_offer, self).fields_view_get(cr, user, new_view_id[0], view_type, context, toolbar,)# submenu=submenu) for trunk client
        else:
            result = super(dm_offer, self).fields_view_get(cr, user, view_id, view_type, context, toolbar,)# submenu=submenu) for trunk client
            if 'type' in context:
                if context['type'] == 'model':
                    if 'toolbar' in result:
                        if 'print' in result['toolbar']:
                            new_print = filter(lambda x: x['report_name'] not in
                                        ['offer.report', 'preoffer.report'],
                                        result['toolbar']['print'])
                            result['toolbar']['print'] = new_print
                if context['type'] == 'preoffer':
                    if 'toolbar' in result:
                        if 'relate' in result['toolbar']:
                            result['toolbar']['relate'] = ''
                        if 'print' in result['toolbar']:
                            new_print = filter(lambda x: x['report_name'] ==
                                'preoffer.report', result['toolbar']['print'])
                            result['toolbar']['print'] = new_print
            else:
                if 'toolbar' in result:
                    if 'print' in result['toolbar'] and 'report' in \
                        result['toolbar'] and result['toolbar']['report']:
#                    if result['toolbar'].has_key('print'):
                        new_print = filter(lambda x: x['report_name'] not in \
                                            ['offer.model.report',
                                             'preoffer.report'],
                                              result['toolbar']['print'])
                        result['toolbar']['print'] = new_print
        return result

    def fields_get(self, cr, uid, fields=None, context=None):
        res = super(dm_offer, self).fields_get(cr, uid, fields, context)
        if context and not 'type' in context and 'type' in res:
            res['type']['selection'] = [('new', 'New'), 
                                        ('standart', 'Standart'),
                                        ('rewrite', 'Rewrite'),
                                        ('as', 'After-Sale')]
        return res

    def default_get(self, cr, uid, fields, context=None):
        value = super(dm_offer, self).default_get(cr, uid, fields, context)
        if not 'create' in context and 'type' in context and \
                                                    context['type'] == 'model':
            value['code'] = self.pool.get('ir.sequence').get(cr, uid,
                                                                    'dm.offer')
        return value

    def create(self, cr, uid, vals, context={}):
        if not 'type' in vals and 'preoffer_type' in vals:
            vals['type'] = 'preoffer'
        elif not 'type' in vals:
            vals['type'] = 'model'
#        context['create'] = 'create'
        new_offer_id = super(dm_offer, self).create(cr, uid, vals, context)
        if 'preoffer_original_id' in vals:
            self.write(cr, uid, vals['preoffer_original_id'],
                       {'preoffer_offer_id': new_offer_id})
        return new_offer_id

    def write(self, cr, uid, ids, vals, context={}):
        if 'preoffer_original_id' in vals:
            self.write(cr, uid, vals['preoffer_original_id'],
                                     {'preoffer_offer_id': ids[0]})
        return super(dm_offer, self).write(cr, uid, ids, vals, context)

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context = {}
        if default is None:
            default = {}

        offer_step_obj = self.pool.get('dm.offer.step')
        document_obj = self.pool.get('dm.offer.document')
        transition_obj = self.pool.get('dm.offer.step.transition')
        plugin_obj = self.pool.get('dm.dtp.plugin')

        offer = self.browse(cr, uid, id)

        default = default.copy()
        default['name'] = 'New offer from model %s' % offer.name
        default['step_ids'] = []

        # offer is copied
        offer_id = super(dm_offer, self).copy(cr, uid, id, default, context)

        offer_step_ids = offer_step_obj.search(cr, uid, [('offer_id', '=', id)])
        offer_steps = offer_step_obj.browse(cr, uid, offer_step_ids)

        # offer step are copied:
        new_steps = []
        for ostep in offer_steps:
            # offer step is copied:
            nid = offer_step_obj.copy(cr, uid, ostep.id, {
                'name': 'New offer step from offer step %s' % ostep.name,
                'offer_id': offer_id,
                'document_ids': [],
                'outgoing_transition_ids': [],
                'incoming_transition_ids': [],
            })

            # documents are copied:
            new_docs = []
            for doc in ostep.document_ids:
                doc_id = document_obj.copy(cr, uid, doc.id, {
                    'name': 'New document from document %s' % doc.name,
                    'step_id': nid,
                    'document_template_plugin_ids': [],
                })
                plugins = []
                for plugin in doc.document_template_plugin_ids:
                    sql = "insert into dm_doc_template_plugin_rel (document_id, document_template_plugin_id) values (%s, %s)"
                    cr.execute(sql, [doc_id, plugin.id])

            new_steps.append({
                'old_id': ostep.id,
                'new_id': nid,
                'o_trans_id': ostep.outgoing_transition_ids,
            })

        # transitions are copied:
        for ostep in new_steps:
            if ostep['o_trans_id']:
                for trans in ostep['o_trans_id']:
                    steps_to = [nid['new_id'] for nid in new_steps if nid['old_id'] == trans.step_to_id.id]
                    if steps_to:
                        step_to = steps_to[0]
                        transition_obj.copy(cr, uid, trans.id, {
                            'step_to_id': step_to,
                            'step_from_id': ostep['new_id'],
                        })
                    else:
                        print "WARNING"
                        print new_steps
                        print trans

        return offer_id

dm_offer() # }}}


class dm_offer_history(osv.osv): # {{{
    _name = "dm.offer.history"
    _order = 'date'
    _columns = {
        'offer_id': fields.many2one('dm.offer', 'Offer', required=True,
                                                            ondelete="cascade"),
        'date': fields.date('Drop Date'),
        'code': fields.char('Code', size=16),
        'responsible_id': fields.many2one('res.users', 'Responsible'),
    }
dm_offer_history() # }}}

class dm_offer_translation(osv.osv): # {{{
    _name = "dm.offer.translation"
    _rec_name = "offer_id"
    _order = "date"
    _columns = {
        'offer_id': fields.many2one('dm.offer', 'Offer', required=True),
        'language_id': fields.many2one('res.lang', 'Language'),
        'translator_id': fields.many2one('res.partner', 'Translator'),
        'date': fields.date('Date'),
        'notes': fields.text('Notes'),
    }
dm_offer_translation() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

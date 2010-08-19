# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import wizard
import pooler

campaign_form = '''<?xml version="1.0"?>
<form string="Add partners to campaign">
    <separator string="Default Values" colspan="4"/>
    <field name="campaign_step_id"/>
    <field name="priority"/>
    <field name="user_id"/>
    <newline/>
    <separator string="Partners" colspan="4"/>
    <field name="partners" nolabel="1" colspan="4"/>
</form>'''

campaign_fields = {
    'campaign_step_id': {'string':'First Campaign Step', 'type':'many2one', 'relation':'campaign.step', 'required':True},
    'priority': {'selection':[('0','Very Low'),('1','Low'),('2','Medium'),('3','Good'),('4','Very Good')], 'string':'Priority', 'type':'selection', 'required':True},
    'user_id': {'string':'User', 'type':'many2one', 'relation':'res.users'},
    'partners': {'string':'Partners', 'type':'many2many', 'required':True, 'relation':'res.partner'}
}

def _partner_add(self, cr, uid, data, context):
    partners = pooler.get_pool(cr.dbname).get('res.partner').browse(cr, uid, data['form']['partners'][0][2])
    campaign_partner_obj = pooler.get_pool(cr.dbname).get('campaign.partner')
    for partner in partners:
        if partner.address:
            campaign_partner_obj.create(cr, uid, {
                'name': partner.name,
                'user_id': data['form']['user_id'],
                'step': data['form']['campaign_step_id'],
                'priority': data['form']['priority'],
                'partner_id': partner.id,
                'part_adr_id': partner.address and partner.address[0].id or False,
                'contact': partner.address and partner.address[0].phone or False,
                'campaign_id': data['id']
            })
    return {}

class part_add(wizard.interface):
    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch':campaign_form, 'fields':campaign_fields, 'state':[('end','Cancel'), ('add','Add these partners')]}
        },
        'add': {
            'actions': [_partner_add],
            'result': {'type':'state', 'state':'end'}
        }
    }
part_add('campaign.partner.add')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


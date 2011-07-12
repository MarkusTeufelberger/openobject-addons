# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Borja López Soilán$
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

"""
Sync with Trac engine and launch the synchronization wizard.
"""
__author__ = "Borja López Soilán (Pexego)"

import netsvc
import wizard
import pooler
import xmlrpclib
import time
import datetime
import re

class trac_syncronizer():
    """
    Sync with Trac engine
    """

    def __init__(self):
        """
        Class init
        """
        self.messages = []
        self.enable_multicall = True


    def log(self, message):
        """
        Aux method to show log information.
        """
        if isinstance(message, unicode):
            smessage = message.encode('utf-8', 'replace')
        else:
            smessage = message
        netsvc.Logger().notifyChannel('trac_sync', netsvc.LOG_INFO, smessage)
        self.messages.append(smessage)


    def _import_trac_ticket(self, cr, uid,
                        project,
                        backlog_name, backlog_facade,
                        trac_facade, ticket_sync_facade,
                        ticket, bitem=None):
        """
        Imports trac tickets (updates or creates a PB in OpenERP)
        """
        if not bitem:
            self.log(u"Importing ticket %s as new %s..." % (ticket[0], backlog_name))
        else:
            self.log(u"Importing ticket %s as %s %s..." % (ticket[0], backlog_name, bitem.id))
            assert bitem.code_trac == ticket[0]
        assert ticket[0] > 0

        ticket_data = ticket[3]
        assert len(ticket_data) > 0

        pool = pooler.get_pool(cr.dbname)

        values = {}

        if backlog_name in ('S'): # ------------------------------------------
            assert ticket_data['type'] == project.ticket_type_story

            # --- scrum ---
            # name
            values['name'] = ticket_data.get('summary')
            # note
            values['note'] = ticket_data.get('description')
            # (active)
            # project_id   [many2one scrum.project]
            values['project_id'] = project.id
            # user_id   [many2one res.users]
            if ticket_data.get('owner'):
                res = pool.get('res.users').search(cr, uid, [('login', '=', ticket_data['owner'])])
                if len(res) > 0:
                    assert len(res) == 1
                    values['user_id'] = res[0]
            # sprint_id   [many2one scrum.sprint]
            if ticket_data.get('sprint'):
                res = pool.get('scrum.sprint').search(cr, uid, [
                            ('project_id', '=', project.id),
                            ('name', '=', ticket_data['sprint'])
                        ])
                if len(res) > 0:
                    assert len(res) == 1
                    values['sprint_id'] = res[0]
                else:
                    self.log(u"WARN: Sprint unknown in ticket %s: %s" % (ticket[0], ticket_data['sprint']))
            # (sequence)
            # priority   [('4','Very Low'), ('3','Low'), ('2','Medium'), ('1','Urgent'), ('0','Very urgent')]
            if ticket_data.get('priority') in ('very low'):
                values['priority'] = '4'
            elif ticket_data.get('priority') in ('low'):
                values['priority'] = '3'
            elif ticket_data.get('priority') in ('medium'):
                values['priority'] = '2'
            elif ticket_data.get('priority') in ('urgent'):
                values['priority'] = '1'
            elif ticket_data.get('priority') in ('very urgent'):
                values['priority'] = '0'
            else:
                self.log(u"WARN: Priority unknown in ticket %s: %s" % (ticket[0], ticket_data.get('priority')))
            # (tasks_id)
            # state
            if ticket_data.get('status') in ('new', 'assigned', 'accepted', 'closed', 'reopened'):
                values['state'] = ticket_data['status']
            else:
                self.log(u"WARN: State unknow in ticket %s: %s" % (ticket[0], ticket_data.get('status')))

            # --- pxgo_scrum_trac ---
            # code
            values['code'] = ticket_data.get('code')
            # code_trac
            values['code_trac'] = ticket[0]
            # component_name
            values['component_name'] = ticket_data.get('component', '')

        elif backlog_name in ('R','T'): # ------------------------------------------
            assert ticket_data['type'] == project.ticket_type_task
            assert False, "Not implemented"

        else:
            self.log(u"ERROR: Backlog type unknown: %s" % backlog_name)
            return False

        if not bitem: # Create new bitem
            try:
                # Creates new bitem
                bitem_id = backlog_facade.create(cr, uid, values)
                #
                # Creates synchronization or update it
                #
                ticket_sync_ids = ticket_sync_facade.search(cr, uid, [
                            ('project_id', '=', project.id),
                            ('ticket', '=', values['code_trac'])
                        ])
                if len(ticket_sync_ids) > 0: # Update
                    ticket_sync_facade.write(cr, uid, ticket_sync_ids, {
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'import_new'
                            })
                else: # New
                    ticket_sync_facade.create(cr, uid, {
                                'project_id': project.id,
                                'ticket': values['code_trac'],
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'import_new'
                            })
                self.log(u"...ready, created: %s." % bitem_id)
                return True
            except Exception, err:
                self.log(u"ERROR: Error creating %s: %s" % (backlog_name, err))
                return False
        else: # Updates exist bitem
            try:
                # Write the bitem
                backlog_facade.write(cr, uid, [bitem.id], values)
                #
                # Writes synchronization registry
                #
                ticket_sync_ids = ticket_sync_facade.search(cr, uid, [
                            ('project_id', '=', project.id),
                            ('ticket', '=', bitem.code_trac)
                        ])
                if len(ticket_sync_ids) > 0:
                    ticket_sync_facade.write(cr, uid, ticket_sync_ids, {
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'import'
                            })
                else:
                    ticket_sync_facade.create(cr, uid, {
                                'project_id': project.id,
                                'ticket': values['code_trac'],
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'import'
                            })
                self.log(u"...ready, writed.")
                return True
            except Exception, err:
                self.log(u"ERROR: Error writing %s %s: %s" % (backlog_name, bitem.id, err))
                return False


    def _import_new_trac_ticket(self, cr, uid,
                        project,
                        backlog_name, backlog_facade,
                        trac_facade, ticket_sync_facade,
                        ticket):
        """
        Importe new trac ticket (delegated in _import_trac_ticket)
        """
        return self._import_trac_ticket(cr, uid,
                                    project,
                                    backlog_name, backlog_facade,
                                    trac_facade, ticket_sync_facade,
                                    ticket,
                                    bitem=None)


    def _export_backlog_item(self, cr, uid,
                        project,
                        backlog_name, backlog_facade,
                        trac_facade, ticket_sync_facade,
                        bitem, ticket=None):
        """
        Export a (PB) to Trac (updates a ticket in Trac)
        """

        if not ticket:
            self.log(u"Exporting %s %s as new ticket..." % (backlog_name, bitem.id))
        else:
            self.log(u"exporting %s %s as ticket %s" % (backlog_name, bitem.id, bitem.code_trac))
            assert bitem.code_trac > 0
            assert ticket[0] == bitem.code_trac

        if ticket:
            ticket_data = ticket[3]
        else:
            ticket_data = None

        values = {}

        if backlog_name in ('S'): # ------------------------------------------

            #    'status': 'assigned',
            if bitem.state in ('new', 'assigned', 'accepted', 'closed', 'reopened'):
                values['status'] = bitem.state
            else:
                self.log(u"WARN: Unknown state in bitem %s: %s" % (bitem.id, bitem.state))
            #    'code': 'RP 11.4',
            values['code'] = bitem.code
            #    'description': u'Updates the...',
            values['description'] = bitem.note
            #    'reporter': 'borjals',
            if bitem.user_id:
                if ticket_data and ticket_data.get('reporter', None):
                    values['reporter'] = bitem.user_id.login
            #    'i_links': '',
            #    'component': u'Test',
            values['component'] = bitem.component_name
            #    'owner': 'borjals',
            if bitem.user_id:
                values['owner'] = bitem.user_id.login
            #    'remaining_time': '8',
            if bitem.state in ('closed', 'done'):
                values['remaining_time'] = '0'
            else:
                values['remaining_time'] = "%.1f" % bitem.remaining_hours
            #    'summary': u'Example',
            values['summary'] = bitem.name
            #    'priority': 'low',
            if bitem.priority in ('4'):
                values['priority'] = 'very low'
            elif bitem.priority in ('3'):
                values['priority'] = 'low'
            elif bitem.priority in ('2'):
                values['priority'] = 'medium'
            elif bitem.priority in ('1'):
                values['priority'] = 'urgent'
            elif bitem.priority in ('0'):
                values['priority'] = 'very urgent'
            else:
                self.log(u"WARN: Unknow priority in bitem %s: %s" % (bitem.id, bitem.priority))
            #    'story_priority': 'Required',
            #    'milestone': 'M2 - Initial version',
            #    'keywords': '',
            #    'rd_points': '2',
            rd_points = (float(bitem.initial_estimation) / 8.0)
            if rd_points < 1 and rd_points > 0:
                values['rd_points'] = "%.1f" % rd_points
            else:
                values['rd_points'] = "%d" % int(rd_points)
            #    'o_links': '',
            #    'type': 'product_backlog',
            values['type'] = ticket_data and ticket_data.get('type', None) or project.ticket_type_story
            #    'sprint': 'Third sprint'
            if bitem.sprint_id:
                values['sprint'] = bitem.sprint_id.name

        elif backlog_name in ('R','T'): # ------------------------------------------
            assert False, "Not implemented"

        else:
            self.log(u"ERROR: Unknown backlog type: %s" % backlog_name)
            return False

        if not ticket: # Creates new ticket
            assert len(values) > 0
            summary = values.pop('summary')
            description = values.pop('description')
            try:
                # Nota:
                #        int ticket.create(string summary, string description, struct attributes={}, boolean notify=False)
                #          Create a new ticket, returning the ticket ID.
                ticket_id = trac_facade.ticket.create(summary, description, values)
                if ticket_id:
                    assert ticket_id > 0
                    # Updates the OpenERP bitem with ticket:
                    backlog_facade.write(cr, uid, [bitem.id], { 'code_trac': ticket_id })
                    bitem.code_trac = ticket_id
                    # Creates synchronization registry
                    ticket_sync_facade.create(cr, uid, {
                                'project_id': project.id,
                                'ticket': ticket_id,
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'export_new'
                            })
                self.log(u"...ready, created: %s." % ticket_id)
                return True
            except Exception, err:
                self.log(u"ERROR: Error creating el %s: %s \n\tSummary: %s\n\tDescription: %s\n\tValues: %s"
                            % (backlog_name, err, summary, description, repr(values)))
                return False
        else: # Updates if bitem exists
            #
            # Deletes nochaged fields
            #
            for fieldname in ['code', 'component', 'remaining_time', 'rd_points', 'reporter']:
                if fieldname not in values:
                    values[fieldname] = ticket_data.get(fieldname, '')

            try:
                # Note:
                #        array ticket.update(int id, string comment, struct attributes={}, boolean notify=False)
                #          Update a ticket, returning the new ticket in the same form as getTicket().
                assert len(values) > 0
                comment = "(Updated by OpenERP TracSync)"
                res = trac_facade.ticket.update(bitem.code_trac, comment, values)
                assert res and len(res) > 0
                #
                # Write synchronization registry
                #
                ticket_sync_ids = ticket_sync_facade.search(cr, uid, [
                            ('project_id', '=', project.id),
                            ('ticket', '=', bitem.code_trac)
                        ])
                if len(ticket_sync_ids) > 0:
                    ticket_sync_facade.write(cr, uid, ticket_sync_ids, {
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'export'
                            })
                else:
                    ticket_sync_facade.create(cr, uid, {
                                'project_id': project.id,
                                'ticket': bitem.code_trac,
                                'sync_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'sync_action': 'export'
                            })
                self.log(u"...ready, write.")
                return True
            except Exception, err:
                self.log(u"ERROR: Error writing %s %s: %s" % (backlog_name, bitem.id, err))
                return False


    def _export_new_backlog_item(self, cr, uid,
                        project,
                        backlog_name, backlog_facade,
                        trac_facade, ticket_sync_facade,
                        bitem):
        """
        Export new (PB) to Trac (delegated in _export_backlog_item)
        """
        assert bitem.code_trac == 0
        return self._export_backlog_item(cr, uid,
                                    project,
                                    backlog_name, backlog_facade,
                                    trac_facade, ticket_sync_facade,
                                    bitem, ticket=None)


    def _query_trac_tickets(self, trac_facade, trac_query):
        """
        Gets all tickets from Trac as result of query
        and returns a indexed distionary by tickets id.
        """
        try:
            ticket_ids = trac_facade.ticket.query(trac_query)
        except xmlrpclib.Fault, err:
            raise wizard.except_wizard(
                    "Error getting ids from Trac tickets",
                    "Error %s: %s" % (err.faultCode, err.faultString))
        tickets = {}
        if self.enable_multicall: # Gets all ticket in one time (fastest)
            multicall = xmlrpclib.MultiCall(trac_facade)
            for ticket_id in ticket_ids:
                multicall.ticket.get(ticket_id)
            try:
                for ticket in multicall():
                    tickets[ticket[0]] = ticket
            except xmlrpclib.Fault, err:
                raise wizard.except_wizard(
                        "Error getting data from Trac tickets",
                        "Error %s: %s" % (err.faultCode, err.faultString))
        else: # Gets tickets one by one (slowest, easy of debug)
            for ticket_id in ticket_ids:
                try:
                    self.log(u"Getting ticket %s" % ticket_id)
                    ticket = trac_facade.ticket.get(ticket_id)
                    tickets[ticket[0]] = ticket
                except xmlrpclib.Fault, err:
                    raise wizard.except_wizard(
                            "Error getting data from Trac ticket %s" % ticket_id,
                            "Error %s: %s" % (err.faultCode, err.faultString))
        return tickets


    def _do_sync_backlog(self, cr, uid,
                        project_id,
                        backlog_name, backlog_facade,
                        trac_facade, ticket_sync_facade,
                        trac_query):
        """
        Syncs a backlog (customer or product) against Trac tickets
        returned by query.
        """

        #
        # Load project data
        #
        scrum_project_facade = pooler.get_pool(cr.dbname).get('scrum.project')
        project = scrum_project_facade.browse(cr, uid, project_id)

        #
        # Gets ids (Product backlog)
        # Then load tickets data and save then in a dictionary according to his ticket code
        #
        self.log(u"Getting %ss from Trac..." % backlog_name)
        tickets = self._query_trac_tickets(trac_facade, trac_query)
        self.log(u"...ready, got %s tickets." % len(tickets))

        #
        # Gets (produyct backlogs) of OpenERP (only ids)
        #
        self.log(u"Getting %ss from OpenERP..." % backlog_name)
        bitem_ids = backlog_facade.search(cr, uid, [('project_id', '=', project_id)])
        self.log("...ready, got %s %ss." % (len(bitem_ids), backlog_name))

        #
        # Load product backlogs from OpenERP and compared his date
        #   with Tract tickets for deciding to do: export or import.
        #
        tickets_to_import = [] # List of tickets to import
        bitems_to_export = [] # List of (PB) to export (or create in Trac)
        tickets_in_openerp = {} # Dictionary (by code) of tickets for (PB) in OpenERP
        self.log(u"Processing backlog (%s)..." % backlog_name)
        for bitem in backlog_facade.browse(cr, uid, bitem_ids):

            if bitem.code_trac:
                # Gets associated ticket (of dictionary)
                ticket = tickets.get(bitem.code_trac, None)
                if ticket:
                    # Marks ticket as used/fixed
                    tickets_in_openerp[bitem.code_trac] = ticket

                    #
                    # Gets last synchronization date
                    #
                    ticket_sync_ids = ticket_sync_facade.search(cr, uid, [
                                ('project_id', '=', project_id),
                                ('ticket', '=', bitem.code_trac)
                            ])
                    if len(ticket_sync_ids) > 0:
                        assert len(ticket_sync_ids) == 1, "Must be only one backlog ticket for ticket %s (found: %s)" % (bitem.code_trac, repr(ticket_sync_ids))
                        res = ticket_sync_facade.browse(cr, uid, ticket_sync_ids)
                        ticket_sync = res[0]
                        sync_date = ticket_sync.sync_date # "2009-07-28 14:34:58.632334"
                        sync_date = datetime.datetime.strptime(sync_date[:19], "%Y-%m-%d %H:%M:%S")
                        # Inserts small margin of time, because otherwise
                        # sync_date and bitem_date easily will coincide.
                        sync_date = sync_date + datetime.timedelta(seconds=15)
                    else:
                        sync_date = datetime.datetime.strptime("1971-01-01", "%Y-%m-%d")

                    #
                    # Gets date of last modification in OpenERP
                    #
                    res = backlog_facade.perm_read(cr, uid, [bitem.id])
                    bitem_date = res[0]['write_date'] # "2009-07-28 14:31:58.638574"
                    if not bitem_date:
                        bitem_date = res[0]['create_date']
                    bitem_date = datetime.datetime.strptime(bitem_date[:19], "%Y-%m-%d %H:%M:%S")

                    #
                    # Gets last modification adte in Trac
                    #
                    ticket_date = ticket[2] # <DateTime '20090729T14:30:26' at 9d8f0ec>
                    ticket_date = datetime.datetime.strptime(str(ticket_date), "%Y%m%dT%H:%M:%S")

                    #
                    # Gets the time difference and converts
                    # Trac date to comparable format.
                    #
                    timezone_delta = datetime.timedelta(hours=(project.xmlrpc_timezone_diff_hours or 0))
                    ticket_date = ticket_date + timezone_delta

                    #
                    # Checks if there have been changes since
                    #   the last synchronization, note:
                    #   only consider modificaciones a nivel de minuto.
                    #
                    if (bitem_date >= sync_date) or (ticket_date >= sync_date):
                        #
                        # There are modification from the last synchronization
                        #
                        if (bitem_date > ticket_date):
                            bitems_to_export.append(bitem)
                        if (bitem_date < ticket_date):
                            tickets_to_import.append(ticket)
                else:
                    self.log(u"ERROR: " \
                            "Cannot get the ticket (%s) related to %s %s (%s)"
                            % (bitem.code_trac, backlog_name, bitem.id, bitem.name))
                    self.log(u"WARN: " \
                            "deleting the realationship between %s %s and tickets %s, " \
                            "for renewing ticket " \
                            "in next exportation."
                            % (backlog_name, bitem.id, bitem.code_trac))
                    backlog_facade.write(cr, uid, [bitem.id], { 'code_trac': 0 })
            else:
                bitems_to_export.append(bitem)
        self.log(u"...ready, processed %s %ss." % (len(bitem_ids), backlog_name))

        #
        # Goes around tickets check if any isn't in OpenERP
        #
        self.log(u"Searching new tickets (%s/%s)..." % (len(tickets_in_openerp), len(tickets)))
        old_lenght = len(tickets_to_import)
        for ticket in tickets.itervalues():
            if not ticket[0] in tickets_in_openerp:
                tickets_to_import.append(ticket)
        self.log(u"...ready, finds %s new tickets."
                    % (len(tickets_to_import) - old_lenght))

        #
        # Tickets importarion
        #
        self.log(u"Importing %s tickets from Trac to %ss OpenERP..." % (len(tickets_to_import), backlog_name))
        for ticket in tickets_to_import:
            bitem_ids = backlog_facade.search(cr, uid, [
                            ('project_id', '=', project_id),
                            ('code_trac', '=', ticket[0])
                        ])
            if len(bitem_ids) > 0:
                bitem = backlog_facade.browse(cr, uid, bitem_ids[0])
                self._import_trac_ticket(cr, uid,
                                    project,
                                    backlog_name, backlog_facade,
                                    trac_facade,
                                    ticket_sync_facade,
                                    ticket, bitem)
            else:
                self._import_new_trac_ticket(cr, uid,
                                    project,
                                    backlog_name, backlog_facade,
                                    trac_facade,
                                    ticket_sync_facade,
                                    ticket)
        self.log(u"...ready, imported %s tickets." % len(tickets_to_import))

        #
        # Exportation of (PBs)
        #
        self.log(u"Exporting %s %ss OpenERP tickets to Trac..." % (len(bitems_to_export), backlog_name))
        for bitem in bitems_to_export:
            if bitem.code_trac:
                ticket = tickets[bitem.code_trac]
                self._export_backlog_item(cr, uid,
                                    project,
                                    backlog_name, backlog_facade,
                                    trac_facade,
                                    ticket_sync_facade,
                                    bitem, ticket)
            else:
                self._export_new_backlog_item(cr, uid,
                                    project,
                                    backlog_name, backlog_facade,
                                    trac_facade,
                                    ticket_sync_facade,
                                    bitem)
        self.log(u"...ready, exported %s %ss." % (len(bitems_to_export), backlog_name))


    def sync(self, cr, uid, project_id):
        """
        Syn project with Trac, delegated in _do_sync_backlog for
        each one tickets types (customer backlogs, product backlogs)
        """
        assert project_id > 0
        pool = pooler.get_pool(cr.dbname)
        sp_facade = pool.get('scrum.project')
        project = sp_facade.browse(cr, uid, project_id)
        user = pool.get('res.users').browse(cr, uid, uid)

        if not project.xmlrpc_url \
                or not project.ticket_type_story \
                or not project.ticket_type_task:
            raise wizard.except_wizard("Error",
                    "This project isn't configure correctly.")

        self.log(u"Synchronicing project: %s" % project.name)
        self.log(u"XMLRPC URL of Trac: %s" % project.xmlrpc_url)
        self.log(u"Connecting as user: %s" % user.login)

        match_obj = re.match(r"http://(?P<hostname>.*?)/(?P<project>.*?)/.*", project.xmlrpc_url)

        if not match_obj:
            raise wizard.except_wizard("Error",
                    "The project hasn't a correct Trac url (%s)."
                    % project.xmlrpc_url)

        trac_url = "http://%s:%s@%s/%s/login/xmlrpc" % (
                        user.login, user.password, match_obj.group('hostname'), match_obj.group('project'))
        self.log(u"Connection URL: %s" % trac_url)

        #
        # Connects to xmlrpc interface of Trac
        #
        trac_facade = None
        try:
            self.log(u"Conectando a %s..." % trac_url)
            trac_facade = xmlrpclib.ServerProxy(trac_url)
            self.log(u"...conexion establecida con exito.")
        except xmlrpclib.Fault, err:
            raise wizard.except_wizard("Error en la conexion con Trac.",
                            "Error %s: %s" % (err.faultCode, err.faultString))

        #
        # Syncs the bitems
        #
        backlog_facade = None

        self.log(u"----- User histories (Product backlog) ------")
        backlog_facade = pool.get('scrum.product.backlog')
        trac_query = "max=0&type=%s" % project.ticket_type_story

        ticket_sync_facade = pool.get('pxgo.scrum.trac.ticket_sync')
        self._do_sync_backlog(cr, uid,
                        project_id,
                        'S', backlog_facade,
                        trac_facade, ticket_sync_facade,
                        trac_query)

        return self.messages




#-------------------------------------------------------------------------------
# Wizard
#-------------------------------------------------------------------------------
class trac_sync_wizard(wizard.interface):
    """
    Wizard for OpenERP project synchronization (Scrum) to Trac
    """
    #
    # Pantalla inicial ---------------------------------------------------------
    #

    init_fields = {
        'project_id' : {'type':'many2one', 'relation': 'scrum.project', 'required': True},
    }


    init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="TracSync" colspan="4">
        <label string="Select project to a synchronize:" colspan="4" align="0.0"/>
        <newline/>
        <field string="Project" name="project_id" domain="[('trac_project','&lt;&gt;',False)]"/>
    </form>"""


    def _init_action(self, cr, uid, data, context):
        """
        Get a project (associated to Trac) for showing
        as by default selection.
        """
        scrum_project_facade = pooler.get_pool(cr.dbname).get('scrum.project')

        project_id = None
        if data.get('model') == 'scrum.project':
            project_id = data.get('id')
            project_ids = scrum_project_facade.search(cr, uid, [('trac_project', '<>', False), ('id', '=', project_id)])
            project_id = project_ids and project_ids[0] or None

        return { 'project_id' : project_id }

    #
    # Screen of (results of) synchronization -------------------------------
    #

    sync_fields = {
        'caption': { 'type': 'char', 'size': 255 },
        'message': { 'type': 'text' },
    }


    sync_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="TracSync" colspan="4">
        <field string="Title" name="caption" colspan="4" nolabel="1" readonly="1"/>
        <newline/>
        <label string="------------------------------------------------------------------------------" align="0.0" colspan="4"/>
        <field string="Result" name="message" colspan="4" nolabel="1"/>
    </form>"""

    def _sync_action(self, cr, uid, data, context):
        """
        Syncs project againts Trac using trac_syncronizer
        """
        project_id = data['form']['project_id']
        assert project_id > 0
        engine = trac_syncronizer()
        messages = engine.sync(cr, uid, project_id)
        caption = u"Full synchronization successfully"
        for message in messages:
            if message.startswith('ERROR'):
                caption = u"One or more errors found"
                break
            elif message.startswith('WARN'):
                caption = u"Raise one or more warnings"
                break
        message = ''.join(["%s\n" % x for x in messages])

        return {
                    'message': message,
                    'caption': caption
                }


    states = {
        'init': {
            'actions': [_init_action],
            'result': {
                'type': 'form',
                'arch': init_form,
                'fields': init_fields,
                'state': [('end', 'Cancel'), ('sync', 'Sync')]
            }
        },
        'sync': {
            'actions': [_sync_action],
            'result': {
                'type': 'form',
                'arch': sync_form,
                'fields': sync_fields,
                'state': [('end', 'Acept')]
            }
        },
        'end' : {
            'actions' : [],
            'result': {'type': 'state', 'state': 'end'},
        },
    }
trac_sync_wizard('pxgo_scrum_trac.trac_sync_wizard')







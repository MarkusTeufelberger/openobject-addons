# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai (gdukai@gmail.com)
#    Copyright (C) 2009 Cloves J. G. de Almeida (cjalmeida@gvmail.br)
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
import stomp
from lxml import objectify
from lxml import etree

import netsvc
import pooler
from osv import osv, fields

#modify netsvc.Agent to stop the STOMPAgents, too
#don't know how to do this in a cleaner way
netsvc.Agent._messaging_agents = set()

@classmethod
def quit(cls):
    for agent in cls._messaging_agents:
        agent.stop()
    cls.cancel(None)

netsvc.Agent.quit = quit
#

class Log(netsvc.Logger):
    """syntactic sugar"""

    def debug(self, text):
        self.notifyChannel('mbi', netsvc.LOG_DEBUG, text)

log = Log()

class STOMPAgent(object):
    """Base class to be inherited from by sending and listening agents."""

    def __init__(self, name, dbname):
        self.con_inbox = None
        self.con_outbox = None
        self.name = name
        self.dbname = dbname
        self.fullname = self.dbname + '/' + self.name
        self.queue_name = '/queue/' + self.fullname
        self.config = {}

    def get_connection_parameters(self):
        kwargs = {}
        for param in (
            'host_and_ports',
            'reconnect_sleep_initial',
            'reconnect_attempts_max',
            'host_and_ports',
            'user',
            'passcode',
            'prefer_localhost',
            'try_loopback_connect',
            'reconnect_sleep_initial',
            'reconnect_sleep_increase',
            'reconnect_sleep_jitter',
            'reconnect_sleep_max',
            'reconnect_attempts_max',
            'use_ssl = False',
            'ssl_key_file',
            'ssl_cert_file',
            'ssl_ca_certs',
            'ssl_cert_validator'
            ):
            if hasattr(self.config, param):
                kwargs[param] = getattr(self.config, param)
        return kwargs

    def stop(self):
        if self.con_inbox and self.con_inbox.is_connected():
            self.con_inbox.unsubscribe(destination=self.queue_name)
            self.con_inbox.stop()
        if self.con_outbox and self.con_outbox.is_connected():
            self.con_outbox.stop()

class STOMPListeningAgent(STOMPAgent):
    def __init__(self, name, dbname, listener):
        super(STOMPListeningAgent, self).__init__(name, dbname)
        self.con_inbox = None
        self.listener = listener
        self.listener.agent = self

    def configure_listening(self):
        if self.con_inbox and self.con_inbox.is_connected():
            return
        log.debug('Connecting to the STOMP server for listening')
        self.con_inbox = stomp.Connection(**self.get_connection_parameters())
        self.con_inbox.set_listener(self.fullname, self.listener)
        self.con_inbox.start()
        self.con_inbox.connect()
        self.con_inbox.subscribe(destination=self.queue_name, ack='client')

class STOMPSendingAgent(STOMPAgent):
    def __init__(self, name, dbname):
        super(STOMPSendingAgent, self).__init__(name, dbname)
        self.con_outbox = None

    def configure_sending(self):
        if self.con_outbox and self.con_outbox.is_connected():
            return
        log.debug('Connecting to the STOMP server for sending')
        self.con_outbox = stomp.Connection(**self.get_connection_parameters())
        self.con_outbox.start()
        self.con_outbox.connect()

class STOMPListener(stomp.listener.ConnectionListener):
    """This class' methods are called by the stomppy library
    when receiving messages. Look at the base class for more explanation.
    For generic usage it's enough to implement process_message() and
    the with the received messages there.
    """
    def __init__(self, pool, dbname, uid):
        self.pool = pool
        self.mbi_obj = self.pool.get('mbi')
        self.dbname = dbname
        self.uid = uid
        self.agent = None
        self.log = log
        super(STOMPListener, self).__init__()

    def process_message(self, cr, uid, xml):
        """cr is a transaction opened just for this message
        xml is an lxml.objectify object created from the message
        """
        raise NotImplementedError(
            'You have to implement the process_message() method!')

    def on_message(self, headers, message):
        cr =  pooler.get_db(self.dbname).cursor()
        uid = self.uid
        doc = objectify.fromstring(message)
        try:
            self.process_message(cr, uid, doc)
        except Exception, e:
            cr.rollback()
            cr.close()
            #send the error details in a request
            subject = "MBI OpenERP Error Receiving Message"
            body = str(headers) + "\n\n"
            body += message + "\n\n"
            body += str(e) + "\n\n"
            #mbi serializationerrors have this
            if hasattr(e, 'orig_exception'):
                body += str(e.orig_exception)
            #except_osvs have this
            if hasattr(e, 'value'):
                body += str(e.value)
            req_obj = self.pool.get('res.request')
            cr =  pooler.get_db(self.dbname).cursor()
            req_obj.create(cr, uid, {
                'name' : subject,
                'act_from' : uid,
                'act_to' : 1,
                'body': body,
            })
            cr.commit()
            cr.close()
            raise e
        cr.commit()
        cr.close()
        self.agent.con_inbox.ack(headers)

class mbi(osv.osv):
    _description = 'Message Based Integration Driver'
    _name = "mbi"

    _listening_agents = {}
    _sending_agents = {}
    _sending_agents_ready = False

    def send(self, cr, uid, message, queues):
        if not mbi._sending_agents_ready:
            self.setup_sending_agents(cr, uid)
        for dest in queues:
            agent = mbi._sending_agents[dest]
            try:
                agent.configure_sending()
            except stomp.exception.ReconnectFailedException:
                raise osv.except_osv('STOMP Error',
                    'Could not connect to message broker!')
            agent.con_outbox.send(message, destination='/queue/' + dest,
                persistent='true')

    def consume_generic(self, cr, uid, xml_check, obj_name, root):
        """
        Generic xml consumer. It creates/updates an object from an xml message.
        It relies on the OO object to have a "from_xml" method.
        """

        if root.xpath('count(' + xml_check + ')') > 0:
            obj = self.pool.get(obj_name)
            (action, oid, vals) = obj.from_xml(cr, uid, root)

            if action == 0: #CREATE
                context = {'mbi_propagate': False}
                log.debug("consume_generic: (create, %s, %s)" % (str(vals[False]), str(context)))
                res = obj.create(cr, uid, vals[False], context)
                vals.pop(False)
                for lang, data in vals.iteritems():
                    if not data:
                        continue
                    context['lang'] = lang
                    log.debug("consume_generic: (create, %s, %s)" % (str(data), str(context)))
                    obj.write(cr, uid, [res], data, context)
                return res

            elif action == 1: #UPDATE
                ids = [oid]
                for lang, data in vals.iteritems():
                    if not data:
                        continue
                    context = {'mbi_propagate': False, 'lang': lang}
                    log.debug("consume_generic: (write, %s, %s, %s)" % (str(ids), str(data), str(context)))
                    obj.write(cr, uid, ids, data, context)
                return oid

            else:
                log.debug(etree.tostring(root, pretty_print=True,
                    encoding='utf-8'))
                raise Exception('Action not implemented: %s' % action)

    def scheduler_runs_this(self, cr, uid):
        self.setup_listening_agents(cr, uid)
        for agent in self._listening_agents.values():
            agent.configure_listening()

    def get_listeners(self, cr, uid):
        """Override this to add listeners to queues."""
        return {}

    def get_queues_to_send(self, cr, uid):
        """Override this to add the names of queues to send to."""
        return {}

    def setup_listening_agents(self, cr, uid):
        """Instantiate all listening agents but to start listening
        agent.configure_listening() needs to be called.
        """
        user_obj = self.pool.get('res.users')
        company = user_obj.browse(cr, uid, uid).company_id
        for name, listener_class in self.get_listeners(cr, uid).items():
            if name not in mbi._listening_agents:
                agent = STOMPListeningAgent(name, cr.dbname, listener_class)
                netsvc.Agent._messaging_agents.add(agent)
                mbi._listening_agents[name] = agent
                for param in company.stomp_connection_parameter_ids:
                    mbi._listening_agents[name].config[param.name] \
                        = param.value

    def setup_sending_agents(self, cr, uid):
        """Instantiate all sending agents."""
        user_obj = self.pool.get('res.users')
        company = user_obj.browse(cr, uid, uid).company_id
        for name in self.get_queues_to_send(cr, uid):
            if name not in mbi._sending_agents:
                agent = STOMPSendingAgent(name, cr.dbname)
                netsvc.Agent._messaging_agents.add(agent)
                mbi._sending_agents[name] = agent
                for param in company.stomp_connection_parameter_ids:
                    mbi._listening_agents[name].config[param.name] \
                        = param.value
        mbi._sending_agents_ready = True

mbi()

class stomp_connection_parameter(osv.osv):
    """Connection parameters are optional but if defined, override defaults."""
    _name = 'stomp.connection.parameter'

    _columns = {
        'name': fields.selection([
            ('host_and_ports', 'host_and_ports'),
            ('user', 'user'),
            ('passcode', 'passcode'),
            ('prefer_localhost', 'prefer_localhost'),
            ('try_loopback_connect', 'try_loopback_connect'),
            ('reconnect_sleep_initial', 'reconnect_sleep_initial'),
            ('reconnect_sleep_increase', 'reconnect_sleep_increase'),
            ('reconnect_sleep_jitter', 'reconnect_sleep_jitter'),
            ('reconnect_sleep_max', 'reconnect_sleep_max'),
            ('reconnect_attempts_max', 'reconnect_attempts_max'),
            ('use_ssl', 'use_ssl'),
            ('ssl_key_file', 'ssl_key_file'),
            ('ssl_cert_file', 'ssl_cert_file'),
            ('ssl_ca_certs', 'ssl_ca_certs'),
            ('ssl_cert_validator', 'ssl_cert_validator'),
            ], 'Name', required=True),
        'value': fields.char('Value', size=64, required=True,
            help='Look at stomp.Connection() for description of the parameters.'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
    }

stomp_connection_parameter()
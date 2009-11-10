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

import os
import netsvc
import pooler
import pydot
import tools
import report

def translate_accent(text):
    text = text.encode('utf-8')
    text = text.replace('é','e').replace('è','e').replace('ë','e').replace('ê','e')
    text = text.replace('â','a').replace('à','a')
    text = text.replace('ù','u').replace('û','u')
    text = text.replace('î','i').replace('ï','i')
    text = text.replace('ô','o').replace('ö','o')
    text = text.replace('Â','A').replace('Ä','A')
    text = text.replace('É','E').replace('È','E').replace('Ë','E').replace('Ê','E')
    text = text.replace('Î','I').replace('Ï','I')
    text = text.replace('Ö','O').replace('Ô','O')
    text = text.replace('Ü','U').replace('Û','U').replace('Ù','U')
    return text


def graph_get(cr, uid, graph, offer_id):
    
    offer_obj = pooler.get_pool(cr.dbname).get('dm.offer')
    offer = offer_obj.browse(cr, uid, offer_id)[0]
    nodes = {}
    step_type = pooler.get_pool(cr.dbname).get('dm.offer.step.type')
    type_ids = step_type.search(cr, uid, [])
    for step in offer.step_ids:
        if not step.graph_hide:
            args = {}

            """ Get user language """
            usr_obj = pooler.get_pool(cr.dbname).get('res.users')
            user = usr_obj.browse(cr, uid, [uid])[0]
            user_lang = user.context_lang

            """ Get Code Translation """
            trans_obj =  pooler.get_pool(cr.dbname).get('ir.translation')
            type_trans = trans_obj._get_ids(cr, uid, 'dm.offer.step,code', 
                                    'model', user_lang or 'en_US', [step.id])
            type_code = type_trans[step.id] or step.code
            args['label'] = translate_accent(
                                        type_code +'\\n' + step.media_id.code)

            graph.add_node(pydot.Node(step.id, **args))

    for step in offer.step_ids:
        for transition in step.outgoing_transition_ids:
            if not transition.graph_hide:
                trargs = {
                    'label': translate_accent(transition.condition_id.name + '\\n' + str(transition.delay) + ' ' + transition.delay_type),
                    'arrowtail': 'inv',
                }
                graph.add_edge(pydot.Edge( str(transition.step_from_id.id), 
                        str(transition.step_to_id.id), fontsize="10", **trargs))
    return True



class report_graph_instance(object):
    def __init__(self, cr, uid, ids, data):
        logger = netsvc.Logger()
        try:
            import pydot
        except Exception, e:
            logger.notifyChannel('workflow', netsvc.LOG_WARNING,
                'Import Error for pydot, you will not be able \
                                                        to render workflows\n'
                'Consider Installing PyDot or dependencies: \
                                                http://dkbza.org/pydot.html')
            raise e
        offer_id = ids
        self.done = False

        offer = translate_accent(pooler.get_pool(cr.dbname).get('dm.offer').browse(cr, uid, offer_id)[0].name)

        graph = pydot.Dot(fontsize="16", label=offer, size='10.7, 7.3',
                          center='1', ratio='auto', rotate='90', rankdir='LR' )

        graph_get(cr, uid, graph, offer_id)

        ps_string = graph.create_ps(prog='dot')
        if os.name == "nt":
            prog = 'ps2pdf.bat'
        else:
            prog = 'ps2pdf'
        args = (prog, '-', '-')
        try:
            _input, output = tools.exec_command_pipe(*args)
        except:
            return
        _input.write(ps_string)
        _input.close()
        self.result = output.read()
        output.close()
        self.done = True

    def is_done(self):
        return self.done

    def get(self):
        if self.done:
            return self.result
        else:
            return None

class report_graph(report.interface.report_int):
    def __init__(self, name, table):
        report.interface.report_int.__init__(self, name)
        self.table = table

    def result(self):
        if self.obj.is_done():
            return (True, self.obj.get(), 'pdf')
        else:
            return (False, False, False)

    def create(self, cr, uid, ids, data, context={}):
        self.obj = report_graph_instance(cr, uid, ids, data)
        return (self.obj.get(), 'pdf')

report_graph('report.dm.offer.graph', 'dm.offer')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    

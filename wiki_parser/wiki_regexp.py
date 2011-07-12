# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Pexego (<www.pexego.es>). All Rights Reserved
#    $Santiago Argüeso Armesto$
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
from osv import fields, osv, orm

import re

EXPRESSION_REGEX = re.compile(u"""
    \{\{
    (?!\s*((if|condition|for(each)?)-(start|end)|(subreport|include))\s+)
    (?P<expression>.+?)
    \}\}
    """, re.UNICODE | re.X | re.S)

#
# 'Block' regex, that is, loop ('foreach'/'for') and conditional ('if') blocks.
#
BLOCK_REGEX = re.compile(u"""
    (
        # Loop block (for/foreach)
            # Loop start (ex. [[foreach-start name='loop1' item='object' in='objects']]):
                \{\{\s*
                for(each)?-start\s+
                name\s*                 = \s*(”|“|"|&apos;)(?P<for_name>\w+)(”|“|"|&apos;)\s*
                item\s*                 = \s*(”|“|"|&apos;)(?P<for_item>\w+)(”|“|"|&apos;)\s*
                (in|collection|col)\s*  = \s*(”|“|"|&apos;)(?P<for_collection>.+?)(”|“|"|&apos;)\s*
                \}\}
            # Loop content
                (?P<for_content>.+)
            # Loop end (ex. [[foreach-end name='loop']]
                \{\{\s*
                for(each)?-end\s+
                name\s*?                =\s*?(”|“|"|&apos;)(?P=for_name)(”|“|"|&apos;)\s*
                \}\}
    |
        # Conditional block (if)
            # Conditional start (ex [[if-start name='test1' condition='something == True']]):
                \{\{\s*
                (if|condition)?-start\s+
                name\s*                 = \s*(”|“|"|&apos;)(?P<if_name>\w+)(”|“|"|&apos;)\s*
                (value|eval|condition)\s*
                                        = \s*(”|“|"|&apos;)(?P<if_condition>.+?)(”|“|"|&apos;)\s*
                \}\}
            # Conditional content when true
                (?P<if_content>.+)
            # Else branch
                (
                # Else start (ex [[else name='test1']])
                    \{\{\s*
                    else\s+
                    name\s*?            =\s*?(”|“|"|&apos;)(?P=if_name)(”|“|"|&apos;)\s*
                    \}\}
                # Conditional content when false (optional)
                    (?P<if_else_content>.+)
                )?
            # Conditional end (ex [[if-end name='test1']]):
                \{\{\s*
                if(condition)?-end\s+
                name\s*?                =\s*?(”|“|"|&apos;)(?P=if_name)(”|“|"|&apos;)\s*
                \}\}
    )
    """, re.UNICODE | re.X | re.S )



#-------------------------------------------------------------------------------
# Utility functions
#-------------------------------------------------------------------------------

def log(message, level="DEBUG"):
    """
    Logs messages using the OpenErp facilities if available
    """
    try:
        import netsvc
        if level == "DEBUG":
            nlevel = netsvc.LOG_DEBUG
        elif level == "INFO":
            nlevel = netsvc.LOG_INFO
        elif level == "WARN":
            nlevel = netsvc.LOG_WARNING
        elif level == "ERROR":
            nlevel = netsvc.LOG_ERROR
        netsvc.Logger().notifyChannel('odt_report_engine', nlevel, message)
    except:
        try:
            print "%s: %s" % (level, message)
        except:
            print "%s: %s" % (level, message.encode('ascii', 'replace'))

#-------------------------------------------------------------------------------
# 'Parser' functions
#-------------------------------------------------------------------------------

ODT_ENCODING = "UTF-8"

def unescape(text):
    """
    Unescape some characters.
    """
    new_text = text
    if text != None and len(text) > 0:
        new_text = re.sub(u"&apos;", "'", new_text)
        new_text = re.sub(u"(”|“)", "'", new_text)
        new_text = re.sub(u"<text:s/>", " ", new_text)
        new_text = re.sub(u"<text:line-break/>", "\n", new_text)

    return new_text


def escape(text):
    """
    Escape some characters.
    """
    new_text = text
    if text != None and len(text) > 0:
        new_text = re.sub(u"'", "&apos;", new_text)
        new_text = re.sub(u'\b"', "“", new_text)
        new_text = re.sub(u'"\b', "”", new_text)
        new_text = re.sub(u"  ", " <text:s/>", new_text)
        new_text = re.sub(u"\n", "<text:line-break/>", new_text)
    return new_text

def process_code(data, context):
    """
    Unescapes and evaluates some embeded Python code.
    """
    #escaped_data = unescape(data)
    escaped_data = data
    eval_data = eval(escaped_data, context)
    if type(eval_data) == type(str()):
        eval_data = unicode(eval_data,'UTF-8')
        pass
    return eval_data

    
def process_expressions(data, context):
    """
    Process all the expressions (see expression_regex) inside a block
    (or at the top level), evaluating them as Python code
    using the specified 'context'.
    """
    def eval_expression(match, context):
        """
        Evaluates an expression in the current 'context'.
        """
        text = match.group('expression')
        evaluated_text = process_code(text, context)
        evaluated_text2 = unicode(evaluated_text)
        #evaluated_text3 = escape(evaluated_text2)
        evaluated_text = evaluated_text2
        log(u"== Expression '%s' => '%s'" % (text, evaluated_text))
        return evaluated_text

    # Replace all the expressions with their value.
    new_data = re.sub(EXPRESSION_REGEX, lambda x: eval_expression(x, context), data)
    return new_data


def process_blocks(data, context):
    """
    Process all the blocks (loops, conditionals) inside a block
    (or at the top level), calling himself recursively for each inner block,
    and calling process_expressions in the end.
    """
    def eval_block(match, context):
        """
        Evaluates a block in the current 'context'
        """
        new_data = ''

        if match.group('if_name'):
            #
            # Conditional blocks -----------------
            #
            if_name = match.group('if_name')
            if_condition = match.group('if_condition')
            if_content = match.group('if_content')
            else_content = match.group('if_else_content')
            log("=> If %s" % if_name)
            if_context = context # Note: its not a copy!
            if process_code(if_condition, context):
                log("== if branch")
                new_content = process_content(if_content, if_context)
            elif (else_content):
                log("== else branch")
                new_content = process_content(else_content, if_context)
            else:
                new_content = ''
            new_data = "%s%s" % (new_data, new_content)
            log("<= If %s" % if_name)

        elif match.group('for_name'):

            #
            # Loop blocks -----------------
            #
            for_name = match.group('for_name')
            for_item = match.group('for_item')
            for_collection = match.group('for_collection')
            for_content = match.group('for_content')
            log("=> For %s" % for_name)
            for element in process_code(for_collection, context):
                log("== For %s loop (%s)" % (for_name, element))
                for_context = context # Note: its not a copy!
                for_context[for_item] = element
                new_content = process_content(for_content, for_context)
                new_data = "%s%s" % (new_data, new_content)
            log("<= For %s" % for_name)
        else:
            raise Exception("ERROR: Unknown block type!")

        return new_data

    # Replace all the blocks with their value.
    if type(data) == type(str()):
        data = unicode(data,'UTF-8')

    new_data = re.sub(BLOCK_REGEX, lambda b: eval_block(b, context), data)
    return new_data




def process_content(data, context):
    """
    Processes a block or file (top level) contents.
    """
    # First process blocks at the top level (will recurse)
    new_data = process_blocks(data, context)
    # Then expressions at the top level
    new_data = process_expressions(new_data, context)
    # Then subreports at the top level
    #new_data = process_subreports(new_data, context)
    return new_data


class Wiki(osv.osv):
    _inherit="wiki.wiki"

    def onchange_group_id(self, cr, uid, ids, group_id, content, context={}):
        """Copia imágenes del grrupo wiki a la página wiki para respetar las plantillas"""
        f_attach = self.pool.get ('ir.attachment')
        attach_ids = f_attach.search(cr,uid,[
                                    ('res_model', '=', 'wiki.groups'),
                                    ('res_id', '=', group_id)
                                ])
        for id in ids:
            for attach in f_attach.browse(cr, uid, attach_ids):
                vals= {
                    'name':attach.name +"_"+str(id),
                    'datas':attach.datas,
                    'datas_fname':attach.datas_fname,
                    'description':attach.description,
                    'res_model':'wiki.wiki',
                    'res_id': id
                }
                print vals
                f_attach.create(cr,uid,vals)
        return super(Wiki, self).onchange_group_id(cr, uid, ids, group_id, content, context)


    def create (self, cr, uid, vals, context={}):
       
        ids = super(Wiki, self).create(cr, uid, vals)
        if 'text_area' in vals:
            self.write(cr,uid,[ids],{'text_area':vals['text_area']})
        return ids

    def write (self, cr, uid, ids, vals, context={}):
        if 'text_area' in vals:
            vals['text_area']=self.process_wiki_content(cr, uid,ids,vals['text_area'],context)
        return super(Wiki, self).write(cr, uid, ids, vals)



    def process_wiki_content(self,cr, uid,ids,text,context ):
        localcontext = context
        localcontext['object'] = self.pool.get('wiki.wiki').browse(cr, uid, ids, context)[0]
        localcontext['ids'] = ids
        localcontext['model'] = 'wiki.wiki'
        text = process_content(text, localcontext)
        return text

Wiki()
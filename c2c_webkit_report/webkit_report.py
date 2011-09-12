# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
import os
import re
import tempfile
import time
import subprocess

from mako.template import Template

import pooler
import netsvc
import report
from report.report_sxw import *
from osv import osv
from tools.config import config
from tools.translate import _

from report_helper import WebKitHelper

logger = netsvc.Logger()


def mako_template(text):
    """Build a Mako template.

    This template uses UTF-8 encoding
    """
    # default_filters=['unicode', 'h'] can be used to set global filters
    return Template(text, input_encoding='utf-8', output_encoding='utf-8')


class WebKitParser(report_sxw):
    """Custom class that use webkit to render HTML reports
       Code partially taken from report openoffice. Thanks guys :)
    """

    def __init__(self, name, table, rml=False, parser=False, 
        header=True, store=False):
        self.parser_instance = False
        report_sxw.__init__(self, name, table, rml, parser, 
            header, store)

    def get_lib(self, cursor, uid, company) :
        """Return the lib wkhtml path"""
        #TODO Detect lib in system first
        path = self.pool.get('res.company').read(cursor, uid, company, ['lib_path',])

        if path['lib_path']:
            path = path['lib_path'].replace(u' ','')
        else :
            raise osv.except_osv(
                                _('Webkit executable not set in company'+
                                'Please complete company setting'),
                                _('Path is none')
                                )
        if os.path.isabs(path) :
            if (os.path.exists(path) and os.access(path, os.X_OK) and os.path.basename(path).startswith('wkhtmltopdf')):
                return path
            else:
                raise osv.except_osv(
                                    _('Wrong path set in company'+
                                    'Given path is not executable or path is wrong'),
                                    'for path %s'%(path)
                                    )
        else:
            for syspath in os.environ["PATH"].split(os.pathsep):
                cmd = os.path.join(syspath, path)
                if (os.path.exists(cmd) and os.access(cmd, os.X_OK)):
                    return path

        raise osv.except_osv(
                            _('Please install wkhtmltopdf 0.9.9'+
                            '(sudo apt-get install wkhtmltopdf) '+
                            'or download it from here: '+
                            'http://code.google.com/p/wkhtmltopdf/downloads/list.'+
                            ' You can set executable path into the company'),
                            _('The embedded lib are not anymore present for security reasons')
                            )
        return False

    def generate_pdf(self, comm_path, report_xml, header, footer, html_list, webkit_header=False):
        """Call webkit in order to generate pdf"""
        if not webkit_header:
            webkit_header = report_xml.webkit_header
        tmp_dir = tempfile.gettempdir()
        out = report_xml.name+str(time.time())+'.pdf'
        out = os.path.join(tmp_dir, out.replace(' ',''))
        files = []
        file_to_del = []
        if comm_path:
            command = [comm_path]
        else:
            command = ['wkhtmltopdf']

        command.append('--quiet')
        # default to UTF-8 encoding.  Use <meta charset="latin-1"> to override.
        command.extend(['--encoding', 'utf-8'])
        if header:
            head_file = file( os.path.join(
                                  tmp_dir,
                                  str(time.time()) + '.head.html'
                                 ),
                                'w'
                            )
            head_file.write(header)
            head_file.close()
            file_to_del.append(head_file.name)
            command.extend(['--header-html', head_file.name])
        if footer:
            foot_file = file(  os.path.join(
                                  tmp_dir,
                                  str(time.time()) + '.foot.html'
                                 ),
                                'w'
                            )
            foot_file.write(footer)
            foot_file.close()
            file_to_del.append(foot_file.name)
            command.extend(['--footer-html', foot_file.name])

        if webkit_header.margin_top :
            command.extend(['--margin-top', str(webkit_header.margin_top).replace(',', '.')])
        if webkit_header.margin_bottom :
            command.extend(['--margin-bottom', str(webkit_header.margin_bottom).replace(',', '.')])
        if webkit_header.margin_left :
            command.extend(['--margin-left', str(webkit_header.margin_left).replace(',', '.')])
        if webkit_header.margin_right :
            command.extend(['--margin-right', str(webkit_header.margin_right).replace(',', '.')])
        if webkit_header.orientation :
            command.extend(['--orientation', str(webkit_header.orientation).replace(',', '.')])
        if webkit_header.format :
            command.extend(['--page-size', str(webkit_header.format).replace(',', '.')])

        additional_args = self.parser_instance.localcontext.get('additional_args', False)
        if additional_args:
            for arg in additional_args:
                command.extend(arg)

        count = 0
        for html in html_list :
            html_file = file(os.path.join(tmp_dir, str(time.time()) + str(count) +'.body.html'), 'w')
            count += 1
            html_file.write(html)
            html_file.close()
            file_to_del.append(html_file.name)
            command.append(html_file.name)
        command.append(out)
        generate_command = ' '.join(command)
        try:
            status = subprocess.call(command, stderr=subprocess.PIPE) # ignore stderr
            if status :
                raise osv.except_osv(
                                _('Webkit raise an error' ),
                                status
                            )
        except Exception:
            for f_to_del in file_to_del :
                os.unlink(f_to_del)

        pdf = file(out, 'rb').read()
        for f_to_del in file_to_del :
            os.unlink(f_to_del)

        os.unlink(out)
        return pdf
    # Typo Error Backward compatibility 
    genreate_pdf = generate_pdf

    def translate_call(self, src):
        """Translate String."""
        ir_translation = self.pool.get('ir.translation')
        name = self.name
        if name.startswith('report.'):
            name = name.lstrip('report.')
        res = ir_translation._get_source(self.parser_instance.cr, self.parser_instance.uid, name, 'rml', self.parser_instance.localcontext.get('lang', 'en_US'), src)
        if not res :
            res = src
        return res

    # override needed to keep the attachments' storing procedure
    def create_single_pdf(self, cursor, uid, ids, data, report_xml, 
        context=None):
        """generate the PDF"""
        if report_xml.report_type != 'webkit':
            return super(WebKitParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)
        self.parser_instance = self.parser(
                                            cursor, 
                                            uid, 
                                            self.name2, 
                                            context=context
                                        )
        self.pool = pooler.get_pool(cursor.dbname)
        objs = self.getObjects(cursor, uid, ids, context)
        self.parser_instance.set_context(objs, data, ids, report_xml.report_type)
        template = None
        if report_xml.report_webkit :
            path = os.path.join(config['addons_path'], report_xml.report_webkit)
            if os.path.exists(path) :
                template = file(path).read()
        if not template and report_xml.report_webkit_data :
            template =  report_xml.report_webkit_data
        if not template :
            raise osv.except_osv(_('Report template not found !'), _(''))

        additional_args = self.parser_instance.localcontext.get('additional_args', False)
        # if a header or footer is defined as text in wkhtmltopdf arguments, we do not create html header/footer
        text_header = set([arg[0] for arg in additional_args]).intersection(['--header-left', '--header-center', 'header-right'])
        text_footer = set([arg[0] for arg in additional_args]).intersection(['--footer-left', '--footer-center', 'footer-right'])
        header = False
        footer = False

        if not text_header:
            header = report_xml.webkit_header.html
        if not text_footer:
            footer = report_xml.webkit_header.footer_html

        if not header and report_xml.header:
            raise osv.except_osv(
                _('No header defined for this report header html is empty !'), 
                _('look in company settings')
            )
        if not report_xml.header and not text_header :
            #I know it could be cleaner ...
            header = u"""
<html>
    <head>
        <style type="text/css"> 
            ${css}
        </style>
        <script>
        function subst() {
           var vars={};
           var x=document.location.search.substring(1).split('&');
           for(var i in x) {var z=x[i].split('=',2);vars[z[0]] = unescape(z[1]);}
           var x=['frompage','topage','page','webpage','section','subsection','subsubsection'];
           for(var i in x) {
             var y = document.getElementsByClassName(x[i]);
             for(var j=0; j<y.length; ++j) y[j].textContent = vars[x[i]];
           }
         }
        </script>
    </head>
<body style="border:0; margin: 0;" onload="subst()">
</body>
</html>"""
        css = report_xml.webkit_header.css
        if not css :
            css = ''
        user = self.pool.get('res.users').browse(cursor, uid, uid)
        company= user.company_id
        body_mako_tpl = mako_template(template)

        helper = WebKitHelper(cursor, uid, report_xml.id, context)
        self.parser_instance.localcontext.update({'setLang': self.parser_instance.setLang})
        self.parser_instance.localcontext.update({'formatLang': self.parser_instance.formatLang})
        html = body_mako_tpl.render(
                                    helper=helper, 
                                    css=css,
                                    _=self.translate_call,
                                    **self.parser_instance.localcontext
                                    )
        head = False
        if header:
            head_mako_tpl = mako_template(header)
            head = head_mako_tpl.render(
                                        helper=helper,
                                        css=css,
                                        _=self.translate_call,
                                        _debug=False,
                                        **self.parser_instance.localcontext
                                    )
        foot = False
        if footer :
            foot_mako_tpl = mako_template(footer)
            foot = foot_mako_tpl.render(
                                        helper=helper,
                                        css=css,
                                        _=self.translate_call,
                                        **self.parser_instance.localcontext
                                        )
        if report_xml.webkit_debug :
            deb = body_mako_tpl.render(
                                        helper=helper,
                                        css=css, 
                                        _debug=tools.ustr(html),
                                        _=self.translate_call,
                                        **self.parser_instance.localcontext
                                        )
            return (deb, 'html')
        
        bin = self.get_lib(cursor, uid, company.id)
        pdf = self.generate_pdf(bin, report_xml, head, foot, [html])
        return (pdf, 'pdf')

    def create_source_webkit(self, cursor, uid, ids, data, report_xml, context=None):
        """We override the create_source_webkit function in order to handle attachement
           Code taken from report openoffice. Thanks guys :) """
        if not context:
            context = {}
        pool = pooler.get_pool(cursor.dbname)
        attach = report_xml.attachment
        if attach:
            objs = self.getObjects(cursor, uid, ids, context)
            results = []
            for obj in objs:
                aname = eval(attach, {'object':obj, 'time':time})
                result = False
                if report_xml.attachment_use and aname and context.get('attachment_use', True):
                    aids = pool.get('ir.attachment').search(
                                                            cursor, 
                                                            uid,
                                                            [
                                                                ('datas_fname','=',aname+'.pdf'),
                                                                ('res_model','=',self.table),
                                                                ('res_id','=',obj.id)
                                                            ]
                                                        )
                    if aids:
                        brow_rec = pool.get('ir.attachment').browse(cursor, uid, aids[0])
                        if not brow_rec.datas:
                            continue
                        d = base64.decodestring(brow_rec.datas)
                        results.append((d,'pdf'))
                        continue
                result = self.create_single_pdf(cursor, uid, [obj.id], data, report_xml, context)
                try:
                    if aname:
                        name = aname+'.'+result[1]
                        pool.get('ir.attachment').create(cursor, uid, {
                            'name': aname,
                            'datas': base64.encodestring(result[0]),
                            'datas_fname': name,
                            'res_model': self.table,
                            'res_id': obj.id,
                            }, context=context
                        )
                        cursor.commit()
                except Exception, exp:
                    import traceback, sys
                    tb_s = reduce(lambda x, y: x+y, traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
                    logger.notifyChannel(
                                                    'report', 
                                                    netsvc.LOG_ERROR, 
                                                    str(exp)
                                                )
                results.append(result)
            if len(results) == 1:
                return results[0]
            else:
                if results[0][1]=='pdf':
                    from report.pyPdf import PdfFileWriter, PdfFileReader
                    output = PdfFileWriter()
                    for r in results:
                        reader = PdfFileReader(cStringIO.StringIO(r[0]))
                        for page in range(reader.getNumPages()):
                            output.addPage(reader.getPage(page))
                    s = cStringIO.StringIO()
                    output.write(s)
                    return s.getvalue(), results[0][1]
                
        return self.create_single_pdf(
                                        cursor, 
                                        uid, 
                                        ids, 
                                        data, 
                                        report_xml, 
                                        context
                                    )

    def create(self, cursor, uid, ids, data, context=None):
        """We override the create function in order to handle generator
           Code taken from report openoffice. Thanks guys :) """
        pool = pooler.get_pool(cursor.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cursor, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_xml_ids:
            
            report_xml = ir_obj.browse(
                                        cursor, 
                                        uid, 
                                        report_xml_ids[0], 
                                        context=context
                                    )
            report_xml.report_rml = None
            report_xml.report_rml_content = None
            report_xml.report_sxw_content_data = None
            report_rml.report_sxw_content = None
            report_rml.report_sxw = None
        else:
            return super(WebKitParser, self).create(cursor, uid, ids, data, context)
        if report_xml.report_type != 'webkit' :
            return super(WebKitParser, self).create(cursor, uid, ids, data, context)
        fnct_ret = self.create_source_webkit(cursor, uid, ids, data, report_xml, context)
        if not fnct_ret:
            return (False,False)
        return fnct_ret

def register_report(name, model, tmpl_path, parser):
    name = 'report.%s' % name
    if netsvc.service_exist( name ):
        #service = netsvc.SERVICES[name].parser
        if isinstance( netsvc.SERVICES[name], WebKitParser ):
            return
        del netsvc.SERVICES[name]
    WebKitParser(name, model, tmpl_path, parser=parser)
    
old_register_all = report.interface.register_all

def new_register_all(db):
    value = old_register_all(db)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM ir_act_report_xml")
    records = cursor.dictfetchall()
    cursor.close()
    for record in records:
        if record['report_type'] in ('webkit',):
            parser=rml_parse
            register_report( record['report_name'], record['model'], record['report_rml'], parser)
    return value

report.interface.register_all = new_register_all

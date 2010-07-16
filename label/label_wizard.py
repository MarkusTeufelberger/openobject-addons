# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (C) 2009  Sharoon Thomas (some code belongs to poweremail module)
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
from osv import osv, fields
import netsvc
import tools
from tools.translate import _
from report.interface import report_rml
import pooler
import re
import os

try:
    from mako.template import Template as MakoTemplate
    from mako import exceptions
except:
    LOGGER.notifyChannel(
                         _("Label"),
                         netsvc.LOG_ERROR,
                         _("Mako templates not installed")
                         )


def get_value(cursor, user, recid, message=None, template=None, context=None):
    """
    Evaluates an expression and returns its value
    @param cursor: Database Cursor
    @param user: ID of current user
    @param recid: ID of the target record under evaluation
    @param message: The expression to be evaluated
    @param template: BrowseRecord object of the current template
    @param context: Open ERP Context
    @return: Computed message (unicode) or u""
    """
    pool = pooler.get_pool(cursor.dbname)
    if message is None:
        message = {}
    #Returns the computed expression
    if message:
        try:
            message = tools.ustr(message)
            object = pool.get(template.model_int_name).browse(cursor, user, recid, context)
            env = {
                'user':pool.get('res.users').browse(cursor, user, user, context),
                'db':cursor.dbname,
            }
            templ = MakoTemplate(message, input_encoding='utf-8')
            reply = MakoTemplate(message).render_unicode(object=object,
                                                         peobject=object,
                                                         env=env,
                                                         format_exceptions=True)
            return reply or False
        except Exception:
            return u""
    else:
        return message


def size2cm(text):
    """Converts the size text ended with 'cm' or 'in' to the numeric value in cm and returns it"""
    if text:
        if text[-2:] == "cm":
            return float(text[:-2])
        elif text[-2:] == "in":
            return float(text[:-2]) * 2.54
    return 0


class report_custom(report_rml):
    def create_xml(self, cr, uid, ids, data, context):

        pool = pooler.get_pool(cr.dbname)

        # Gets data from label wizard form
        vals = pool.get('label.wizard').browse(cr, uid, ids[0])
        vals.printer_top    = size2cm(vals.printer_top)
        vals.printer_bottom = size2cm(vals.printer_bottom)
        vals.printer_left   = size2cm(vals.printer_left)
        vals.printer_right  = size2cm(vals.printer_right)
        vals.page_width = size2cm(vals.label_format.landscape and vals.label_format.pagesize_id.height or vals.label_format.pagesize_id.width)
        vals.page_height = size2cm(vals.label_format.landscape and vals.label_format.pagesize_id.width or vals.label_format.pagesize_id.height)
        vals.rows = vals.label_format.rows
        vals.cols = vals.label_format.cols
        vals.label_width = size2cm(vals.label_format.label_width)
        vals.label_height = size2cm(vals.label_format.label_height)
        vals.width_incr = size2cm(vals.label_format.width_incr)
        vals.height_incr = size2cm(vals.label_format.height_incr)
        vals.initial_left_pos = size2cm(vals.label_format.margin_left)

        # initial_bottom_pos = label.pagesize_id.height - label.margin_top - label.label_height
        mtop = size2cm(vals.label_format.margin_top)
        vals.initial_bottom_pos = vals.page_height - mtop - vals.label_height

        # Adding report data
        #print ids, data, context
        report_xml = '''
    <page_width>%s</page_width>
    <page_height>%s</page_height>
    <rows>%s</rows>
    <cols>%s</cols>
    <label_width>%s</label_width>
    <label_height>%s</label_height>
    <width_incr>%s</width_incr>
    <height_incr>%s</height_incr>
    <initial_bottom_pos>%s</initial_bottom_pos>
    <initial_left_pos>%s</initial_left_pos>
    <font_type>%s</font_type>
    <font_size>%s</font_size>
    <printer_top>%s</printer_top>
    <printer_bottom>%s</printer_bottom>
    <printer_left>%s</printer_left>
    <printer_right>%s</printer_right>''' % (
        vals.page_width,
        vals.page_height,
        vals.rows,
        vals.cols,
        vals.label_width,
        vals.label_height,
        vals.width_incr,
        vals.height_incr,
        vals.initial_bottom_pos,
        vals.initial_left_pos,
        vals.font_type,
        vals.font_size,
        vals.printer_top,
        vals.printer_bottom,
        vals.printer_left,
        vals.printer_right
        )

        template = pool.get('label.templates').browse(cr, uid, int(context['template_id']), context)

        path = os.path.abspath( os.path.dirname(__file__) )
        file_in = path+'/report_template.xsl'
        file_out = path+'/../'+template.report_template.report_xsl

        # Open file with generic template
        try:
            f = open(file_in, 'r')
            try:
                generic_template = f.read()
            finally:
                f.close()
        except:
            raise osv.except_osv(_("Error"), _("Generic template file in label folder can not be read."))

        # We compute at the same time the report template (xsl file) and the tag template (to process with Mako)
        rtl = [] # Report Template list to compute the report template
        rtl.append("""<xsl:template match="object" mode="story">\n""")
        rtln = 0 # Report Template list subtemplate number
        ttl = [] # Tag Template list to compute the tag template
        tag_template = ""

        for line in template.def_body_text.split('\n'):
            # Search for Mako control structures like %if %elif %else, %while, %for, %end...
            mako_control = re.findall(r'\s*%\s*(\w+)', line)
            if mako_control:
                # Special control line. We only deal with %for and %endfor sentences to create:
                # - sub-templates stored in new strings in the report template list (rtl)
                # - deeper XML tags in the tag template list (ttl)
                if mako_control[0] == 'for':
                    # Example: %for o in object.address:  =>  <xsl:apply-templates select="object.address"/>
                    # and starts a new subtemplate: <xsl:template match="object.address"> ..... </xsl:template>
                    for_params = re.findall(r'\s*%\s*for\s+([\w\.]+)\s+in\s+([\w\.]+)\s*:', line)
                    if not len(for_params):
                        raise osv.except_osv(_("Error"), _("Template has invalid %%for control sentence in line:\n%s") % line)
                    rtl[rtln] += """    <xsl:apply-templates select="%s"/>\n""" % for_params[0][1]
                    rtl.append("""<xsl:template match="%s">\n""" % for_params[0][1])
                    rtln += 1
                    tline = re.sub(r'(<[^>]*>)', '', line) + "\n<%s>" % for_params[0][1]
                    ttl.append(for_params[0][1])
                elif mako_control[0] == 'endfor':
                    if not len(ttl) or rtln == 0:
                        raise osv.except_osv(_("Error"), _("Template has not balanced %%for and %%endfor control sentences.\nUnexpected %%endfor sentence."))
                    rtl[rtln] += """</xsl:template>\n"""
                    rtln -= 1
                    tline = "</%s>\n" % ttl.pop() + re.sub(r'(<[^>]*>)', '', line)
            else:
                # Normal line to print into the report template replacing field names
                # Example: ${object.country.name or ''}  =>  <xsl:value-of select="object.country.name"/>
                tags = re.findall(r'(</*([\w]+)\s*[^>]*>)', line)
                text_line = True
                for tag in tags:
                    if tag[1] not in ['b', 'i', 'u', 'super', 'sub', 'font', 'barcode', 'greek']: # Only <font> and <barcode> tags are allowed to be included inside text lines
                        text_line = False
                if text_line: # Line that includes text o fields to print
                    rline = re.sub(r'(<([\w/]+)\s*[^>]*>)', r'</xsl:text>\1<xsl:text>', line) # To put <...> report tags outside <xsl:text>...</xsl:text>
                    rline = re.sub(r'\$\{([\w\.]+)\s*[^}]*\}', r'</xsl:text><xsl:value-of select="\1"/><xsl:text>', rline)
                    rline = '    <para style="nospace"><xsl:text>%s</xsl:text></para>\n' % rline
                    tline = re.sub(r'(<[^>]*>)', '', line) # To exclude <...> tags
                    tline = re.sub(r'(\$\{([\w\.]+)\s*[^}]*\})', r'<\2>\1</\2>', tline)
                else: # Line that only includes report tags like <tr>, <td>, <blockTable>, <nextFrame/>, ... to control the report format
                    rline = line + '\n'
                    tline = ''
                rtl[rtln] += rline
            tag_template += tline + '\n'

        if len(ttl) or rtln != 0:
            raise osv.except_osv(_("Error"), _("Template has not balanced %%for and %%endfor control sentences.\nMissing %%endfor sentence(s)."))
        #print tag_template

        rtl[rtln] += "</xsl:template>\n"
        report_template = '\n'.join(rtl)
        report_template = re.sub(r'<xsl:text></xsl:text>', '', report_template) # To remove empty fix strings
        #print report_template

        # Write the report template file (xsl file)
        try:
            f = open(file_out, 'w')
            try:
                f.write(generic_template.encode('utf-8') % (
                    template.report_stylesheets or '',
                    template.sort_field1,
                    template.sort_field2,
                    template.sort_field3,
                    report_template.encode('utf-8')
                ))
            finally:
                f.close()
        except:
            raise osv.except_osv(_("Error"), _("Template file in label/custom_reports folder can not be created."))

        # Adding first empty labels
        info_xml = '\n'
        for i in range((vals.first_row-1) * vals.cols + vals.first_col-1):
            info_xml += '<object></object>\n'

        # Adding partner labels (ids of selected records are in context['active_ids'] in OpenERP 5.0)
        partners = pool.get('res.partner').browse(cr, uid, context['active_ids'])
        for partner in partners:
            value = get_value(cr, uid, partner.id, tag_template, template, context)
            info_xml += '<object>\n%s</object>\n\n' % value

        # Computing the xml
        xml='''<?xml version="1.0" encoding="UTF-8" ?>
<objects>%s%s</objects>''' % (report_xml, info_xml)
        #print xml
        return xml


class label_wizard(osv.osv_memory):
    _name = 'label.wizard'
    _description = 'This is the wizard for create PDF Labels'
    _rec_name = "subject"

    _columns = {
        'state':fields.selection([
                        ('create_report','Create a report.'),
                        ('notify_top','Printer top margin bigger than (top label margin + label height). Try again.'),
                        ('notify_bottom','Printer bottom margin bigger than (bottom label margin + label height). Try again.'),
                        ('notify_left','Printer left margin bigger than (left label margin + label width). Try again.'),
                        ('notify_right','Printer right margin bigger than (right label margin + label width). Try again.'),
                        ('done','Wizard Complete')
                                  ],'Status',readonly=True),
        'label_format': fields.many2one('report.label','Label Format', required=True),
        'printer_top' : fields.char('Top', size=20, required=True, help='Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in'),
        'printer_bottom': fields.char('Bottom', size=20, required=True, help='Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in'),
        'printer_left': fields.char('Left', size=20, required=True, help='Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in'),
        'printer_right': fields.char('Right', size=20, required=True, help='Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in'),
        'font_type': fields.char('Font Type', size=20, required=True, help='Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in'),
        'font_type': fields.selection(
            [('Times-Roman','Times-Roman'),('Times-Bold','Times-Bold'),('Times-Italic','Times-Italic'),('Times-BoldItalic','Times-BoldItalic'),('Helvetica','Helvetica'),('Helvetica-Bold','Helvetica-Bold'),('Helvetica-Oblique','Helvetica-Oblique'),('Helvetica-BoldOblique','Helvetica-BoldOblique'),('Courier','Courier'),('Courier-Bold','Courier-Bold'),('Courier-Oblique','Courier-Oblique'),('Courier-BoldOblique','Courier-BoldOblique')
            ], 'Font Type', required=True),
        'font_size': fields.selection(
            [('6','6'),('7','7'),('8','8'),('9','9'),('10','10'),('11','11'),('12','12'),('14','14')
            ], 'Font Size', required=True),
        'first_row': fields.integer('First Row',help='The Row of the first label in the first page'),
        'first_col': fields.integer('First Column',help='The Column of the first label in the first page'),
    }

    _defaults = {
        'state': lambda *a: 'create_report',
    }

    def create_label(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        vals = self.browse(cr, uid, ids[0], context)
        vals.printer_top    = size2cm(vals.printer_top)
        vals.printer_bottom = size2cm(vals.printer_bottom)
        vals.printer_left   = size2cm(vals.printer_left)
        vals.printer_right  = size2cm(vals.printer_right)
        vals.page_width = size2cm(vals.label_format.landscape and vals.label_format.pagesize_id.height or vals.label_format.pagesize_id.width)
        vals.page_height = size2cm(vals.label_format.landscape and vals.label_format.pagesize_id.width or vals.label_format.pagesize_id.height)
        vals.rows = vals.label_format.rows
        vals.cols = vals.label_format.cols
        vals.label_width = size2cm(vals.label_format.label_width)
        vals.label_height = size2cm(vals.label_format.label_height)
        vals.width_incr = size2cm(vals.label_format.width_incr)
        vals.height_incr = size2cm(vals.label_format.height_incr)
        vals.initial_left_pos = size2cm(vals.label_format.margin_left)

        # initial_bottom_pos = label.pagesize_id.height - label.margin_top - label.label_height
        mtop = size2cm(vals.label_format.margin_top)
        vals.initial_bottom_pos = vals.page_height - mtop - vals.label_height

        validate = False

        if vals.printer_top > mtop + vals.label_height:
            self.write(cr, uid, ids, {'state':'notify_top'}, context)
            validate = True
        if vals.printer_left > vals.initial_left_pos + vals.label_width:
            self.write(cr, uid, ids, {'state':'notify_top'}, context)
            validate = True
        if vals.printer_bottom > vals.page_height - mtop - (vals.rows-1) * vals.height_incr:
            self.write(cr, uid, ids, {'state':'notify_top'}, context)
            validate = True
        if vals.printer_right >  vals.page_width - vals.initial_left_pos - (vals.cols-1) * vals.width_incr:
            self.write(cr, uid, ids, {'state':'notify_top'}, context)
            validate = True

        if not validate:
            template = self.pool.get('label.templates').browse(cr, uid, int(context['template_id']))
            report_full_name = 'report.'+template.report_template.report_name
            if report_full_name in netsvc.SERVICES:
                del netsvc.SERVICES[report_full_name]
            report_custom(report_full_name, template.report_template.model, '', 'addons/'+template.report_template.report_xsl)

            #datas dictionary should work with client >= 5.0.12 (see https://answers.launchpad.net/openobject-server/+question/116262)
            #but web client seems not receiving datas information
            datas = {}
            datas['context'] = context.copy()
            res =  {
                'type': 'ir.actions.report.xml',
                'report_name': template.report_template.report_name,
                'datas': datas,
            }
            return res

label_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

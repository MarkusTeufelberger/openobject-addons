# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenOffice Reports
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
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

"""
OpenOffice Reports - Reporting Engine based on Relatorio and OpenOffice.
"""
__author__ = "Borja López Soilán (Pexego)"

import os
import report
import pooler
import netsvc
import base64
import tempfile
from os.path import splitext
from tools.translate import _
from oo_template import OOTemplate, OOTemplateException



class OOReportException(Exception):
    """
    OpenERP report exception
    """
    def __init__(self, message):
        # pylint: disable-msg=W0231
        self.message = message
    def __str__(self):
        return self.message


class OOReport:
    """
    OpenOffice/Relatorio based report.
    """

    def log(self, message, level=netsvc.LOG_DEBUG):
        """
        Helper method used print debug messages
        """
        netsvc.Logger().notifyChannel('pxgo_openffice_reports', level, message)


    def __init__(self, name, cr, uid, ids, data, context):
        self.name = name
        self.cr = cr
        self.uid = uid
        self.ids = ids
        self.data = data
        self.model = self.data['model']
        self.context = context or {}
        self.dbname = self.cr.dbname
        self.pool = pooler.get_pool( self.cr.dbname )
        self.openoffice_port = 8100
        self.autostart_openoffice = True


    def execute(self, output_format='pdf', report_file_name=None):
        """
        Generate the report.
        """

        def _base64_to_string(field_value):
            """
            Helper method to decode a binary field
            """
            return base64.decodestring(field_value)

        def _get_attachments():
            """
            Helper function that returns a function that
            gets the attachments for one object using the current database
            connection (cr) and user (uid).
            """
            def get_attachments_func(browse_object):
                """
                Returns the attachments for one browse_object
                """
                db, pool = pooler.get_db_and_pool(self.dbname)
                cr = db.cursor()
                att_facade = pool.get('ir.attachment')
                # pylint: disable-msg=W0212
                attachment_ids = att_facade.search(cr, self.uid, [
                        ('res_model', '=', browse_object._name), 
                        ('res_id', '=', browse_object.id)
                    ])
                return att_facade.browse(cr, self.uid, attachment_ids)
            return get_attachments_func

        def _field_to_image(field_value, rotate=None):
            """
            Helper function that decodes and converts a binary field
            into a png image and returns a tuple like the ones Relatorio
            "image:" directive wants.
            """
            from PIL import Image
            data = base64.decodestring(field_value)
            dummy_fd, temp_file_name = tempfile.mkstemp(prefix='openerp_oor_f2i_')
            temp_file = open(temp_file_name, 'wb')
            try:
                temp_file.write(data)
            finally:
                temp_file.close()
            image = Image.open(temp_file_name)
            if rotate:
                image = image.rotate(rotate)
            image.save(temp_file_name, 'png')
            return (open(temp_file_name, 'rb'), 'image/png')


        def _chart_template_to_image(field=None, filename=None, source=None, filepath=None, source_format=None, encoding=None, context=None):
            """
            Method that can be referenced from the template to include
            charts as images.
            When called it will process the file as a chart template,
            generate a png image, and return the data plus the mime type.
            """
            # Field is a binary field with a base64 encoded file that we will
            # use as source if it is specified
            source = field and base64.decodestring(field) or source

            filepath = filepath or filename
            filename = None
            assert filepath

            #
            # Search for the file on the addons folder of OpenERP if the
            # filepath does not exist.
            #
            if not os.path.exists(filepath):
                search_paths = ['./bin/addons/%s' % filepath, './addons/%s' % filepath]
                for path in search_paths:
                    if os.path.exists(path):
                        filepath = path
                        break

            #
            # Genshi Base Template nor it's subclases
            # (NewTextTemplate and chart.Template)
            # seem to load the filepath/filename automatically;
            # so we will read the file here if needed.
            #
            if not source:
                file = open(filepath, 'rb')
                try:
                    source = file.read()
                finally:
                    file.close()

            #
            # Process the chart subreport file
            #
            self.log("Generating chart subreport...")
            from relatorio.templates.chart import Template
            chart_subreport_template = Template(source=source, encoding=encoding)
            data = chart_subreport_template #.generate(**context)
            self.log("...done, chart generated.")

            return (data, 'image/png')




        def _gettext(lang):
            """
            Helper function that returns a function to enable translation
            using the using the current database connection, and language.
            """
            def gettext(text):
                """
                Returns the translation of one string
                """
                cr = pooler.get_db(self.dbname).cursor()
                context = { 'lang': lang }
                return _(text)
            return gettext


        assert output_format

        #
        # Get the report path
        #
        if not report_file_name:
            reports = self.pool.get( 'ir.actions.report.xml' )
            report_ids = reports.search(self.cr, self.uid, [('report_name', '=', self.name[7:])], context=self.context)
            report_file_name = reports.read(self.cr, self.uid, report_ids[0], ['report_rml'])['report_rml']
            path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
            report_file_name = os.path.join(path, report_file_name)

        #
        # Set the variables that the report must see
        #
        context = self.context
        context['objects'] = self.pool.get(self.model).browse(self.cr, self.uid, self.ids, self.context)
        context['ids'] = self.ids
        context['model'] = self.model
        context['data'] = self.data

        #
        # Some aliases used on standard OpenERP reports
        #
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid, self.context)
        context['user'] = user
        context['company'] = user.company_id
        context['logo'] = user.company_id and user.company_id.logo
        context['lang'] = context.get('lang') or (user.company_id and user.company_id.partner_id and user.company_id.partner_id.lang)

        # TODO: add a translate helper like the one rml reports use,

        #
        # Add some helper function aliases
        #
        context['base64_to_string'] = context.get('base64_to_string') or _base64_to_string
        context['b2s'] = context.get('b2s') or _base64_to_string
        context['get_attachments'] = context.get('get_attachments') or _get_attachments()
        context['field_to_image'] = context.get('field_to_image') or _field_to_image
        context['f2i'] = context.get('f2i') or _field_to_image
        context['chart_template_to_image'] = context.get('chart_template_to_image') or _chart_template_to_image
        context['chart'] = context.get('chart') or _chart_template_to_image
        context['gettext'] = context.get('gettext') or _gettext(context.get('lang'))
        context['_'] = context.get('_') or _gettext(context.get('lang'))

        #
        # Process the template using the OpenOffice/Relatorio engine
        #
        data = self.process_template(report_file_name, output_format, context)

        return data


    def process_template(self, template_file, output_format, context=None):
        """
        Will process a relatorio template and return the name
        of the temp output file.
        """
        if context is None: context = {}
        #
        # Get the template
        #
        self.log("Loading template %s from %s" % (self.name, template_file))
        try:
            template = OOTemplate(source=None,
                            filepath=template_file,
                            output_format=output_format,
                            openoffice_port=self.openoffice_port,
                            autostart_openoffice=self.autostart_openoffice,
                            logger=self.log)
        except OOTemplateException, ex:
            raise OOReportException(_("Error loading the OpenOffice template: %s") % ex)

        #
        # Process the template
        #
        self.log("Rendering template %s as %s" % (self.name, output_format))
        try:
            data = template.oo_render(context=context)
        except OOTemplateException, ex:
            raise OOReportException(_("Error processing the OpenOffice template: %s") % ex)

        return data



class openoffice_report(report.interface.report_int):
    """
    Registers an OpenOffice/Relatorio report.
    """

    def __init__(self, name, model, parser=None, context=None):
        if context is None: context = {}
        # Remove report name from list of services if it already
        # exists to avoid report_int's assert. We want to keep the
        # automatic registration at login, but at the same time we
        # need modules to be able to use a parser for certain reports.
        if name in netsvc.SERVICES:
            del netsvc.SERVICES[name]
        super(openoffice_report, self).__init__(name)
        self.model = model
        self.parser = parser
        self._context = context

    def create(self, cr, uid, ids, datas, context=None):
        """
        Register the report with this handler.
        """
        name = self.name

        if self.parser:
            options = self.parser(cr, uid, ids, datas, context)
            ids = options.get('ids', ids)
            name = options.get('name', self.name)
            # Use model defined in openoffice_report definition. Necesary for menu entries.
            datas['model'] = options.get('model', self.model)
            datas['records'] = options.get('records', [])

        self._context.update(context)

        #
        # Find the output format
        #
        reports = pooler.get_pool(cr.dbname).get( 'ir.actions.report.xml' )
        report_ids = reports.search(cr, uid, [('report_name', '=', name[7:])], context=context)
        report_type = reports.read(cr, uid, report_ids[0], ['report_type'])['report_type']
        if report_type.startswith('oo-'):
            output_format = report_type.split('-')[1]
        else:
            output_format = 'pdf'

        #
        # Get the report
        #
        rpt = OOReport( name, cr, uid, ids, datas, self._context )
        return (rpt.execute(output_format=output_format), output_format )






#
# Ugly hack to avoid developers the need to register reports. ------------------
# Based on NaN jasper_reports module.
#

def register_openoffice_report(name, model):
    """
    Registers a report to use the OpenOffice reporting engine.
    """
    name = 'report.%s' % name
    # Register only if it didn't exist another report with the same name
    # given that developers might prefer/need to register the reports themselves.
    # For example, if they need their own parser.
    if netsvc.service_exist( name ):
        if isinstance( netsvc.SERVICES[name], openoffice_report ):
            return
        del netsvc.SERVICES[name]
    openoffice_report( name, model )

#
# This hack allows automatic registration of OpenOffice files without
# the need for developers to register them programatically.
#
OLD_REGISTER_ALL = report.interface.register_all
def new_register_all(db):
    """
    Wrapper around the register_all method of report.interface
    that registers 'automagically' OpenOffice reports.
    """
    # Call the original register_all
    value = OLD_REGISTER_ALL(db)

    #
    # Search for reports with 'oo-<something>' type
    # and register them
    #
    cr = db.cursor()
    cr.execute("SELECT * FROM ir_act_report_xml WHERE report_type LIKE 'oo-%' ORDER BY id")
    records = cr.dictfetchall()
    cr.close()
    for record in records:
        register_openoffice_report( record['report_name'], record['model'] )

    return value

# Chain our method into report.interface:
report.interface.register_all = new_register_all





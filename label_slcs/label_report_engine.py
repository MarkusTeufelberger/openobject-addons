# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Gábor Dukai <gdukai@gmail.com>
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

import os
import tempfile
import shutil
from mako.template import Template as MakoTemplate
from mako.lookup import TemplateLookup

import pooler
import tools
from report.report_sxw import report_sxw

from label.label_report_engine import size2cm
import unaccent

def size2dots(input):
    if input:
        try:
            input / 1
        except TypeError:
            input = size2cm(input)
        #hardcoded dpi: 1mm = 11.8 dots
        dpcm = 118
        return int(round(input * dpcm))
    return 0

class report_label_slcs(report_sxw):

    def create_single_pdf(self, cr, uid, ids, data, report_xml, context=None):
        adp = os.path.abspath(tools.config['addons_path'])
        path = os.path.normcase(os.path.join(adp, 'label_slcs',
            'report', 'label_template.txt'))
        out = open(path).read()
        pool = pooler.get_pool(cr.dbname)
        # Gets data from label wizard form
        vals = pool.get('label.wizard').browse(cr, uid, ids[0])
        vals.cols = vals.label_format.cols
        vals.label_width = size2dots(vals.label_format.label_width)
        vals.label_height = size2dots(vals.label_format.label_height)
        vals.height_incr = size2dots(vals.label_format.height_incr)
        template = pool.get('label.templates').browse(cr, uid, int(context['template_id']), context)
        #
        #Adding labels with object data
        #A list may be passed in context with different quantities
        #for each record. If not, it will use the
        #(ids of selected records are in context['active_ids'] in OpenERP 5.0)
        try:
            obj_list = context['obj_list']
        except KeyError:
            obj_list = [{'id': i, 'qty': 1} for i in context['active_ids']]
        obj_ids = [i['id'] for i in obj_list]
        objects = pool.get(template.model_int_name)\
            .browse(cr, uid, obj_ids, context)
        tmpdir = tempfile.mkdtemp()
        try:
            f = open(os.path.join(tmpdir, 'usertemplate.txt'), 'w')
            f.write(template.def_body_text)
            f.close()
            mylookup = TemplateLookup(directories=[tmpdir])
            user = pool.get('res.users').browse(cr, uid, uid, context)
            out = MakoTemplate(out, lookup=mylookup).render_unicode(
                format_exceptions=True,
                vals=vals, obj_list=obj_list, objects=objects, user=user)
        finally:
            shutil.rmtree(tmpdir)
        out = unaccent.asciify(out)
        return (out, report_xml.report_type)
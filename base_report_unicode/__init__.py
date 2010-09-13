# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009-2010 Gábor Dukai
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

from tools.config import config
import report
import os

def wrap_trml2pdf(method):
    """We have to wrap the original parseString() to modify the rml data
    before it generates the pdf."""
    def convert2TrueType(*args, **argv):
        """This function replaces the type1 font names with their truetype
        substitutes and puts a font registration section at the beginning
        of the rml file. The rml file is acually a string (data)."""
        odata = args[0]
        fontmap = {
            'Times-Roman':                   'DejaVuSerif',
            'Times-BoldItalic':              'DejaVuSerif-BoldItalic',
            'Times-Bold':                    'DejaVuSerif-Bold',
            'Times-Italic':                  'DejaVuSerif-Italic',

            'Helvetica':                     'DejaVuSans',
            'Helvetica-BoldItalic':          'DejaVuSans-BoldOblique',
            'Helvetica-Bold':                'DejaVuSans-Bold',
            'Helvetica-Italic':              'DejaVuSans-Oblique',

            'Courier':                       'DejaVuSansMono',
            'Courier-Bold':                  'DejaVuSansMono-Bold',
            'Courier-BoldItalic':            'DejaVuSansMono-BoldOblique',
            'Courier-Italic':                'DejaVuSansMono-Oblique',

            'Helvetica-ExtraLight':          'DejaVuSans-ExtraLight',

            'TimesCondensed-Roman':          'DejaVuSerifCondensed',
            'TimesCondensed-BoldItalic':     'DejaVuSerifCondensed-BoldItalic',
            'TimesCondensed-Bold':           'DejaVuSerifCondensed-Bold',
            'TimesCondensed-Italic':         'DejaVuSerifCondensed-Italic',

            'HelveticaCondensed':            'DejaVuSansCondensed',
            'HelveticaCondensed-BoldItalic': 'DejaVuSansCondensed-BoldOblique',
            'HelveticaCondensed-Bold':       'DejaVuSansCondensed-Bold',
            'HelveticaCondensed-Italic':     'DejaVuSansCondensed-Oblique',
        }
        i = odata.find('<docinit>')
        if i == -1:
            i = odata.find('<document')
            i = odata.find('>', i)
            i += 1
            starttag = '\n<docinit>\n'
            endtag = '</docinit>'
        else:
            i = i + len('<docinit>')
            starttag = ''
            endtag = ''
        data = odata[:i] + starttag
        adp = os.path.abspath(config['addons_path'])
        for new in fontmap.itervalues():
            fntp = os.path.normcase(os.path.join(adp, 'base_report_unicode', 'fonts', new))
            data += '    <registerFont fontName="' + new + '" fontFile="' + fntp + '.ttf"/>\n'
        data += endtag + odata[i:]
        for  old, new in fontmap.iteritems():
            data = data.replace(old, new)
        return method(data, args[1:] if len(args) > 2 else args[1], **argv)
    return convert2TrueType

report.render.rml2pdf.parseString = wrap_trml2pdf(report.render.rml2pdf.parseString)

report.render.rml2pdf.parseNode = wrap_trml2pdf(report.render.rml2pdf.parseNode)

style_map = {
    'DejaVuSerif': {
        (0, 1): '-Italic',
        (1, 0): '-Bold',
        (1, 1): '-BoldItalic',
    },
    'DejaVuSans': {
        (0, 1): '-Oblique',
        (1, 0): '-Bold',
        (1, 1): '-BoldOblique',
    },
    'DejaVuSansMono': {
        (0, 1): '-Oblique',
        (1, 0): '-Bold',
        (1, 1): '-BoldOblique',
    },
    'DejaVuSerifCondensed': {
        (0, 1): '-Italic',
        (1, 0): '-Bold',
        (1, 1): '-BoldItalic',
    },
    'DejaVuSansCondensed': {
        (0, 1): '-Oblique',
        (1, 0): '-Bold',
        (1, 1): '-BoldOblique',
    },
}

def docinit(self, els):
    """This adds support for <b>, <i> tags for TrueType fonts.
    The original method just ignored them.
    """
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for node in els:
        for font in node.findall('registerFont'):
            name = font.get('fontName').encode('ascii')
            fname = font.get('fontFile').encode('ascii')
            pdfmetrics.registerFont(TTFont(name, fname ))
            addMapping(name, 0, 0, name)    #normal
            for style in ((0, 1), (1, 0), (1, 1)):
                try:
                    addMapping(name,
                        psname=name + style_map[name][style], *style)
                except KeyError:
                    addMapping(name, psname=name, *style)

report.render.rml2pdf.trml2pdf._rml_doc.docinit = docinit

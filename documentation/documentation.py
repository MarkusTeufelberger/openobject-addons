# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 NaN Projectes de Programari Lliure, S.L. All Rights Reserved
#                       http://www.NaN-tic.com
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
import glob
import base64
import codecs
import tempfile
import random
import tools
import re
import psycopg2
from xml import dom
from lxml import etree
from osv import osv
from osv import fields
import netsvc
import ctools 
from tools.translate import _

IdentifierTag = '|||'
ReferenceTag  = '///'


class ir_documentation_paragraph(osv.osv):
    _name = 'ir.documentation.paragraph'
    _description = 'Documentation Paragraph'
    _rec_name = 'identifier'
    _order = 'module_id,filename,sequence'

    def extract_model_data(self, ref):
        ref = ref.replace(' ','')
        ref = ref.strip('/')
        ref = ref.split(':')[1]
        module, dot, id = ref.rpartition('.') #x#x.nodeValue.rpartition('.')
        return module, id

    def extract_extra_options(self, ref):
        ref = ref.replace(' ','')
        ref = ref.strip('/')
        ref = ref.split(':')
        if len(ref) < 3:
            return None
        return ref[2]

    def _menu_references(self, cr, uid, text, context=None):
        references = {}
        menus = re.findall('%s *m *: *\S* *%s' % (ReferenceTag, ReferenceTag), text)
        for ref in menus:
            module, menu = self.extract_model_data(ref)
            ids = self.pool.get('ir.model.data').search(cr, uid, [('module','=',module),('model','=','ir.ui.menu'),('name','=',menu)], context=context)
            data = self.pool.get('ir.model.data').read(cr, uid, ids, ['res_id'], context)

            indent = 0
            for line in text.splitlines():
                if ref in line:
                    indent = len(line) - len( line.lstrip(' ') )
                    break

            references[ref] = {
                'module': module,
                'menu': menu,
                'id': data and data[0]['res_id'],
                'indent': indent,
            }
        return references

    def _view_references(self, cr, uid, text, context=None):
        references = {}
        views = re.findall('%s *v *: *\S* *(?:: *\S* *)?%s' % (ReferenceTag, ReferenceTag), text)
        for ref in views:
            module, view = self.extract_model_data(ref)
            ids = self.pool.get('ir.model.data').search(cr, uid, [('module','=',module),('model','=','ir.ui.view'),('name','=',view)], context=context)
            data = self.pool.get('ir.model.data').read(cr, uid, ids, ['res_id'], context)

            indent = 0
            for line in text.splitlines():
                if ref in line:
                    indent = len(line) - len( line.lstrip(' ') )
                    break

            field = self.extract_extra_options(ref)

            references[ref] = {
                'module': module,
                'view': view,
                'id': data and data[0]['res_id'],
                'indent': indent,
                'field': field,
            }
        return references

    def _field_references(self, cr, uid, text, context=None):
        references = {}
        fields = re.findall('%s *f *: *\S* *(?:: *\S* *)?%s' % (ReferenceTag, ReferenceTag), text)
        for ref in fields:
            model, field = self.extract_model_data(ref)
            ids = self.pool.get('ir.model.fields').search(cr, uid, [('model','=',model),('name','=',field)], context=context)
            if ids:
                id = ids[0]
            else:
                module, field = self.extract_model_data(ref)
                ids = self.pool.get('ir.model.data').search(cr, uid, [('module','=',module),('model','=','ir.model.fields'),('name','=',field)], context=context)
                if ids:
                    data = self.pool.get('ir.model.data').read(cr, uid, ids, ['res_id'], context)
                    id = data[0]['res_id']
                else:
                    id = False

            indent = 0
            for line in text.splitlines():
                if ref in line:
                    indent = len(line) - len( line.lstrip(' ') )
                    break

            options = self.extract_extra_options(ref)

            references[ref] = {
                'model': model,
                'field': field, 
                'id': id,
                'indent': indent,
                'options': options,
            }
        return references
        
    def _render(self, cr, uid, id, text, image, type, context=None):
        from docutils.core import publish_string, Publisher
        try:
            text = publish_string(text, writer_name='html')
        except Exception, e:
            text = _('Error rendering rsT.')
        return text

    def _html(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for paragraph in self.browse(cr, uid, ids, context):
            result[paragraph.id] = self._render(cr, uid, paragraph.id, paragraph.rst, paragraph.image, paragraph.type, context)
        return result

    def _rst(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for paragraph in self.browse(cr, uid, ids, context):
            result[paragraph.id] = self._replace_references(cr, uid, paragraph, context)
        return result


    _columns = {
        'identifier': fields.char('Identifier', size=200, required=True, help='Unique internal identifier'),
        'module_id': fields.many2one('ir.module.module', 'Module', required=True, ondelete='cascade', help='Module this paragraph pertains. For example, if module X provides documentation for module Y, here you will find Y.'),
        'filename': fields.char('File Name', size=500, help='File name where this paragraph will be stored to (if Inherit field is empty)'),
        'text': fields.text('Text', translate=True, help='Paragraph body'),
        'type': fields.selection([('title','Title'),('paragraph','Paragraph'),
            ('chapter','Chapter'),('section','Section'),('subsection','Subsection'),
            ('subsubsection','Subsubsection'),('note','Note'),('image','Image')], 
            'Paragraph Type', required=True),
        'inherit_id': fields.many2one('ir.documentation.paragraph', 'Inherit'),
        'inheriting_ids': fields.one2many('ir.documentation.paragraph', 'inherit_id', 'Inheriting Paragraphs'),
        'position': fields.selection([('before','Before'),('after','After'),('replace','Replace'),('prepend','Prepend'),('append','Append')], 'Position'),
        'image': fields.binary('Image'),
        'parent_id': fields.many2one('ir.documentation.paragraph', 'Parent Paragraph', ondelete='cascade'),
        'child_ids': fields.one2many('ir.documentation.paragraph', 'parent_id', 'Children Paragraphs'),
        'sequence': fields.integer('Sequence', required=True, help='Position of this paragraph in the file'),
        'rst': fields.function(_rst, method=True, string='rsT', type='text', help='rsT text with tags replaced.'),
        'html': fields.function(_html, method=True, string='HTML', type='text', help="Rendered text"),
        'field_ids': fields.one2many('ir.documentation.field', 'paragraph_id', 'Fields', help='Fields referenced in the paragraph.'),
        'view_ids': fields.one2many('ir.documentation.view', 'paragraph_id', 'Views', help='Views referenced in the paragraph.'),
        'menu_ids': fields.one2many('ir.documentation.menu', 'paragraph_id', 'Menus', help='Menu entries referenced in the paragraph.'),
        'active': fields.boolean('Active'),
        'source_module_id': fields.many2one('ir.module.module', 'Source Module', required=True, ondelete='cascade', help='Module where the documentation file really resides. For example, if module X provides documentation for module Y, here you will find X.'),
    }
    _defaults = {
        'active': lambda *a: True,
    }
    _sql_constraints = [
        ('module_id_identifier_uniq', 'unique(identifier, module_id)', 'You cannot have multiple records with the same id for the same module'),
    ]

    def get_field_headings(self, cr, uid, filter, context):
        model = filter[0]
        field = filter[1]
        result = []
        field_ids = self.pool.get('ir.model.fields').search(cr, uid, [('model_id.model','=',model),('name','=',field)], context=context)
        if not field_ids:
            # Ensure search is *not* called if field_ids = [] as it will return all records
            return []
        ids = self.pool.get('ir.documentation.field').search(cr, uid, [('field_id','in',field_ids)], context=context)
        for field in self.pool.get('ir.documentation.field').browse(cr, uid, ids, context):
            result.append( ('field-%d' % field.id, field.paragraph_id.html) )

        return result

    def get_view_headings(self, cr, uid, filter, context):
        model = filter[0]
        view_type = filter[1]
        result = []
        view_ids = self.pool.get('ir.ui.view').search(cr, uid, [('model','=',model),('type','=',view_type)], context=context)
        if not view_ids:
            # Ensure search is *not* called if view_ids = [] as it will return all records
            return []
        ids = self.pool.get('ir.documentation.view').search(cr, uid, [('view_id','in',view_ids)], context=context)
        for view in self.pool.get('ir.documentation.view').browse(cr, uid, ids, context):
            ids = self.pool.get('ir.documentation.screenshot').search(cr, uid, [('paragraph_id','=',view.paragraph_id.id),('user_id','=',uid)], context=context)
            if ids:
                screenshot = self.pool.get('ir.documentation.screenshot').browse(cr, uid, ids[0], context)
                if screenshot.image:
                    image = '<img src="data:image/png;base64,%s" width="200" height="150"/>' % screenshot.image
                    result.append( ('view-%d' % view.id, image) )
        return result

    def get_menu_headings(self, cr, uid, menu_id, context):
        result = []
        ids = self.pool.get('ir.documentation.menu').search(cr, uid, [('menu_id','=',menu_id)], context=context)
        for menu in self.pool.get('ir.documentation.menu').browse(cr, uid, ids, context):
            result.append( ('menu-%d' % menu.id, menu.paragraph_id.html) )

        return result

    def _update_references(self, cr, uid, ids, context):
        for paragraph in self.browse(cr, uid, ids, context):
            # Update field references
            old_ids = self.pool.get('ir.documentation.field').search(cr, uid, [('paragraph_id','=',paragraph.id)], context=context)
            self.pool.get('ir.documentation.field').unlink(cr, uid, old_ids, context)

            fields = self._field_references(cr, uid, paragraph.text, context)
            for reference, data in fields.iteritems():
                if data['options'] == 'help':
                    help = True
                else:
                    help = False
                self.pool.get('ir.documentation.field').create(cr, uid, {
                    'paragraph_id': paragraph.id,
                    'reference': reference,
                    'field_id': data['id'],
                    'indent': data['indent'],
                    'help': help,
                }, context)

            # Update view references
            old_ids = self.pool.get('ir.documentation.view').search(cr, uid, [('paragraph_id','=',paragraph.id)], context=context)
            self.pool.get('ir.documentation.view').unlink(cr, uid, old_ids, context)

            views = self._view_references(cr, uid, paragraph.text, context)
            for reference, data in views.iteritems():
                self.pool.get('ir.documentation.view').create(cr, uid, {
                    'paragraph_id': paragraph.id,
                    'reference': reference,
                    'view_id': data['id'],
                    'indent': data['indent'],
                    'field': data['field'],
                }, context)

            # Update menu references
            old_ids = self.pool.get('ir.documentation.menu').search(cr, uid, [('paragraph_id','=',paragraph.id)], context=context)
            self.pool.get('ir.documentation.menu').unlink(cr, uid, old_ids, context)

            menus = self._menu_references(cr, uid, paragraph.text, context)
            for reference, data in menus.iteritems():
                self.pool.get('ir.documentation.menu').create(cr, uid, {
                    'paragraph_id': paragraph.id,
                    'reference': reference,
                    'menu_id': data['id'],
                    'indent': data['indent'],
                }, context)

    def write(self, cr, uid, ids, vals, context=None):
        result = super(ir_documentation_paragraph, self).write(cr, uid, ids, vals, context)
        if 'text' in vals:
            self._update_references(cr, uid, ids, context)
        return result

    def create(self, cr, uid, vals, context=None):
        id = super(ir_documentation_paragraph, self).create(cr, uid, vals, context)
        if 'text' in vals:
            self._update_references(cr, uid, [id], context)
        return id

    def _import_documentation_module(self, cr, uid, module, doc_directory, source_module, context):
        logger = netsvc.Logger()

        all_files = glob.glob( os.path.join( doc_directory, '*.rst' ) )
        all_files.sort()

        if all_files:
            logger.notifyChannel('documentation', netsvc.LOG_INFO, "Importing documentation of module %s" % module)

        i = 0
        sequence = 1
        for filename in all_files:
            i += 1
            logger.notifyChannel('documentation', netsvc.LOG_INFO, "Importing file #%d: %s" % (i, filename) )
            f = open(filename)
            try:
                rst = f.read()
            finally:
                f.close()

            db_filename = filename.replace( os.path.join(doc_directory,''), '')
            sequence = self.import_rst(cr, uid, module, rst, db_filename, doc_directory, source_module, context, sequence)

    def _import_documentation(self, cr, uid, context):
        cr.execute('DELETE FROM ir_documentation_paragraph')

        addons = tools.config['addons_path']
        modules = glob.glob( os.path.join( addons, '*' ) )
        modules.sort()

        # Add all modules and directories to be processed in a list
        pending_modules = {}
        for module_directory in modules:
            module = os.path.split( module_directory )[1]

            doc_directory = os.path.join( module_directory, 'doc' )
            if os.path.exists( os.path.join( doc_directory, 'modules' ) ):
                submodules = glob.glob( os.path.join( module_directory, 'doc', 'modules', '*' ) )
                submodules.sort()
                for submodule_directory in submodules:
                    submodule = os.path.split( submodule_directory )[1]
                    pending_modules[submodule] = {
                        'directory': submodule_directory,
                        'source_module': module,
                    }
            elif os.path.exists( doc_directory ):
                doc_directory = os.path.join( module_directory, 'doc' )
                #self._import_documentation_module( cr, uid, module, doc_directory, context )
                pending_modules[module] = {
                    'directory': doc_directory,
                    'source_module': module,
                }

        # Add dependency information to all modules to be processed
        for module, data in pending_modules.iteritems():
            ids = self.pool.get('ir.module.module').search(cr, uid, [('name','=',module)], context=context)
            data['dependencies'] = []
            if ids:
                for dependency in self.pool.get('ir.module.module').browse(cr, uid, ids[0], context).dependencies_id:
                    if dependency.name in pending_modules:
                        data['dependencies'].append( dependency.name )

        # Import documentation in order, honouring dependencies
        while pending_modules:
            found = False
            for module in pending_modules.keys():
                if not len(pending_modules[module]['dependencies']):
                    directory = pending_modules[module]['directory']
                    source_module = pending_modules[module]['source_module']
                    self._import_documentation_module( cr, uid, module, directory, source_module, context )
                    del pending_modules[module]
                    found = True
                    # Remove the module from dependencies in other modules that depend on it.
                    for m, d in pending_modules.iteritems():
                        if module in d['dependencies']:
                            d['dependencies'].remove( module )
            if not found:
                raise osv.except_osv(_('Documentation Import Error'), _('There is an error in module dependencies. Documentation for the following modules cannot be imported: %s.' % ', '.join( pending_modules.keys() ) ) )

        return True

    def _replace_references(self, cr, uid, paragraph, context):
        if context is None:
            context = {}

        text = paragraph.text
        # Replace field references
        for field in paragraph.field_ids:
            if not field.field_id:
                continue

            if field.help:
                field_description = self.pool.get('ir.translation')._get_source(cr, uid, '%s,%s' % (field.field_id.model_id.model,field.field_id.name), 'help', context.get('lang','en_US'))
            else:
                field_description = self.pool.get('ir.translation')._get_source(cr, uid, '%s,%s' % (field.field_id.model_id.model,field.field_id.name), 'field', context.get('lang','en_US'))
            text = text.replace(field.reference, field_description)

            # Add anchor at the beginning of the paragraph
            anchor = '%s.. _field_%d:\n\n' % (' ' * field.indent, field.id)
            text = anchor + text

        # Replace view references
        for view in paragraph.view_ids:
            if not view.view_id:
                continue
            view_ids = self.pool.get('ir.documentation.screenshot').search(cr, uid, [('paragraph_id','=',paragraph.id),('user_id','=',uid),('view_id','=',view.view_id.id),('field','=',view.field)], context=context)

            if not view_ids:
                continue

            view_id = view_ids[0]
            image  = '\n'
            # Add anchor 
            image += ' ' * view.indent + '.. _view_%d:\n' % view.id
            # Add image
            image += ' ' * view.indent + '.. image:: view_%d.png\n' % view_id
            image += ' ' * view.indent + '   :align: center\n'
            text = text.replace(view.reference, image)

        # Replace menu references
        for menu in paragraph.menu_ids:
            text = text.replace( menu.reference, '*%s*' % menu.menu_id.complete_name )
            # Add anchor at the beginning of the paragraph
            anchor = '%s.. _menu_%d:\n\n' % (' ' * menu.indent, menu.id)
            text = anchor + text

        # Replace images
        if '.. image::' in paragraph.text:
            idx = paragraph.text.index('.. image::')
            text = text[:idx + len('.. image::')]
            text += ' paragraph_image_%d.png' % paragraph.id

        return text

    def export_rst_helper(self, cr, uid, main_paragraph, before, text, after, context):
        for paragraph in main_paragraph.inheriting_ids:
            partext = self._replace_references( cr, uid, paragraph, context )

            if paragraph.position == 'before':
                before.insert( 0, partext )
            elif paragraph.position == 'after':
                after.append( partext )
            elif paragraph.position == 'prepend':
                text = '%s\n%s' % (partext, text)
            elif paragraph.position == 'append':
                text = '%s\n%s' % (text, partext)
            elif paragraph.position == 'replace':
                text = ctools.stripped( partext )

            text = self.export_rst_helper(cr, uid, paragraph, before, text, after, context)

        return text

    def export_rst(self, cr, uid, context):
        inherits = []
        documentation = {}

        srcdir = tempfile.mkdtemp()

        ids = self.search(cr, uid, [('inherit_id','=',False)], order='filename, sequence', context=context)
        for paragraph in self.browse(cr, uid, ids, context):
            # Take into account documentation of installed modules only
            if paragraph.module_id.state != 'installed':
                continue
            before = []
            after = []
            partext = self._replace_references(cr, uid, paragraph, context)
            text = self.export_rst_helper(cr, uid, paragraph, before, partext, after, context)
            if not paragraph.filename in documentation:
                documentation[paragraph.filename] = []
            documentation[paragraph.filename] += before
            documentation[paragraph.filename].append( text )
            documentation[paragraph.filename] += after

            # Export images of paragraphs
            if paragraph.image:
                f = open( os.path.join( srcdir, 'paragraph_image_%d.png' % paragraph.id ), 'w' )
                try:
                    f.write( base64.decodestring( paragraph.image ) )
                finally:
                    f.close()

        for filename in documentation:
            documentation[filename] = '\n\n'.join( documentation[filename] )


        conf_py = "" 
        conf_py += "master_doc = 'index'\n"
        conf_py += "project = u'OpenERP'\n"
        # pdf (rst2pdf) builder specific
        conf_py += "pdf_documents = [\n"
        conf_py += "('index', u'OpenERP', u'OpenERP', u'Author Name'),\n"
        conf_py += "]\n"
        conf_py += "pdf_stylesheets = ['sphinx','kerning','a4']\n"
        # latex builder specific
        conf_py += "latex_documents = ["
        conf_py += "('index', 'OpenERP.tex', u'OpenERP', u'', 'manual'),"
        conf_py += "]"

        f = open( os.path.join( srcdir, 'conf.py' ), 'w' )
        try:
            f.write( conf_py )
        finally:
            f.close()

        for filename in documentation:
            f = codecs.open( os.path.join( srcdir, filename ), 'w', 'utf-8' )
            try:
                f.write( documentation[filename] )
            finally:
                f.close()

        screenshot_ids = self.pool.get('ir.documentation.screenshot').search(cr, uid, [('user_id','=',uid)], context=context)
        for screenshot in self.pool.get('ir.documentation.screenshot').browse(cr, uid, screenshot_ids, context):
            if not screenshot.image:
                continue
            f = open( os.path.join( srcdir, 'view_%d.png' % screenshot.id ), 'w')
            try:
                f.write( base64.decodestring( screenshot.image ) )
            finally:
                f.close()

        return srcdir

    def create_id(self, cr, uid, module, value, context):
        found = False
        word_count = 7
        while True:
            words = ctools.unaccent( value.strip() ).lower()
            words = words.replace(':','_')
            words = words.replace('.','_')
            words = words.replace('_',' ')
            words = words.split()
            identifier = '_'.join( words[:word_count] )
            ids = self.search(cr, uid, [('module_id.name','=',module),('identifier','=',identifier),'|',('active','=',True),('active','=',False)], context=context)
            if not ids:
                found = True
                break
            word_count += 1
            if word_count > len(words):
                break
        if not found:
            identifier += '_%s' % int(random.random() * 1000000)
        return identifier

    def export_to_pdf(self, cr, uid, context):
        srcdir = self.export_rst(cr, uid, context)
 
        from sphinx.application import Sphinx

        outdir = tempfile.mkdtemp()
        sphinx = Sphinx( srcdir, srcdir, outdir, outdir, 'latex' )
        sphinx.build()

        print "Source dir: ", srcdir
        print "Output dir: ", outdir
        import subprocess
        subprocess.call(['pdflatex', os.path.join( outdir, 'OpenERP.tex' )], cwd=outdir)
        
        pdf = os.path.join( outdir, 'OpenERP.pdf' )
        if os.path.exists( pdf ):
            f = open( pdf )
            try:
                pdf = f.read()
            finally:
                f.close()
            pdf = base64.encodestring(pdf)
        else:
            pdf = None
        return pdf


    def export_to_html(self, cr, uid, context):
        srcdir = self.export_rst(cr, uid, context)

        from sphinx.application import Sphinx

        outdir = tempfile.mkdtemp()
        #sphinx = Sphinx( srcdir, srcdir, outdir, outdir, 'html' )
        sphinx = Sphinx( srcdir, srcdir, outdir, outdir, 'singlehtml' )
        sphinx.build()

        ids = self.pool.get('ir.documentation.file').search(cr, uid, [('user_id','=',uid)], context=context)
        self.pool.get('ir.documentation.file').unlink(cr, uid, ids, context)
        for path, dirnames, filenames in os.walk( outdir ):
            for filename in filenames:
                full = os.path.join( path, filename )
                f = open( full )
                data = base64.encodestring( f.read() )
                f.close()

                self.pool.get('ir.documentation.file').create(cr, uid, {
                    'filename': full.strip( outdir ),
                    'data': data,
                    'user_id': uid,
                }, context)

        print "Source dir: ", srcdir
        print "Output dir: ", outdir


    def import_rst(self, cr, uid, default_module, rst, filename, path, source_module, context, sequence=1):
        logger = netsvc.Logger()

        id = None
        automatic_id = False
        inherit = None
        inherit_id = False
        position = None
        text = ''
        id_line = ''

        source_module_ids = self.pool.get('ir.module.module').search(cr, uid, [('name','=',source_module)], context=context)
        if not source_module_ids:
            raise osv.except_osv(_('Documentation Error'), _('Source module "%s" does not exist') % source_module )
        source_module_id = source_module_ids[0]

        for line in rst.split('\n'):
            stripped = line.strip()

            if stripped.startswith( IdentifierTag ) and stripped.endswith( IdentifierTag ):
                id = stripped.strip(IdentifierTag)
                automatic_id = False
                continue

            if stripped != '':
                if not id:
                    id = self.create_id( cr, uid, default_module, stripped, context )
                    if id:
                        automatic_id = True
                        #print "Paragraph has no identifier, one was created: %s" % id
                text += line + '\n'
                continue

            if stripped == '' and not id:
                # Ignore any leading empty lines
                continue

            if stripped == '' and id and not text:
                # Allow empty lines between id and it's paragraph
                continue

            if not id:
                print "No valid ID could be created for paragraph:%s\n%s\n%s" % (IdentifierTag, text, IdentifierTag)

            if ':' in id:
                if len(id.split(':')) != 3:
                    raise osv.except_osv(_('Invalid documentation'), _('The following ID is not valid:\n%s') % id)
                id = id.split(':')
                position = id[1].strip()
                inherit = id[2].strip()
                id = id[0].strip()

                if not id:
                    text_line = text.splitlines()[0]
                    id = self.create_id( cr, uid, default_module, text_line, context )
                    if id:
                        automatic_id = True

                inherit = inherit.split('.')
                if len(inherit) == 1:
                    module = default_module
                    name = inherit[0]
                else:
                    module = inherit[0]
                    name = inherit[1]

                inherit_ids = self.search(cr, uid, [('module_id.name','=',module),('identifier','=',name)], context=context)
                if not inherit_ids:
                    raise osv.except_osv( _('Documentation Error'), _('Could not find paragraph %s.%s') % (module, name) )
                inherit_id = inherit_ids[0]

            if '.' in id:
                module = id.split('.')[0]
                id = id.split[1]
            else:
                module = default_module

            module_ids = self.pool.get('ir.module.module').search(cr, uid, [('name','=',module)], context=context)
            if not module_ids:
                raise osv.except_osv(_('Documentation Error'), _('Module "%s" does not exist') % module )

            module_id = module_ids[0]

            if isinstance(text, str):
                text = unicode(text, 'utf-8')

            if automatic_id:
                count = 1
                original_id = id
                while True:
                    ids = self.search(cr, uid, [('identifier','=',id),('module_id','=',module_id)], context=context)
                    if not ids:
                        break
                    id = '%s_%d' % ( original_id, count )
                    count += 1


            image_data = False
            if '.. image::' in text:
                idx = text.index('.. image::')
                image = text[idx + len('.. image::'):].strip()
                image = os.path.join( path, image )
                if os.path.exists( image ):
                    logger.notifyChannel('documentation', netsvc.LOG_INFO, "Image file %s not found." % module)
                    f = open(image)
                    try:
                        image_data = f.read()
                    finally:
                        f.close()
                    image_data = base64.encodestring( image_data )

            record_id = self.create(cr, uid, {
               'identifier': id,
               'inherit_id': inherit_id,
               'position': position,
               'module_id': module_id,
               'filename': filename,
               'sequence': sequence,
               'type': ctools.paragraph_type( text ),
               'text': ctools.normalize( text ),
               'image': image_data,
               'source_module_id': source_module_id,
            }, context)
            paragraph = self.browse(cr, uid, id, context)

            # Ensure paragraphs will be exported to translation templates by adding all paragraphs
            # to ir.model.data
            self.pool.get('ir.model.data').create(cr, uid, {
                'module': source_module_id,
                'model': 'ir.documentation.paragraph',
                'name': '%s_%s' % (module, id),
                'res_id': record_id,
            }, context)

            sequence += 1
            text = ''
            id = False
        return sequence

ir_documentation_paragraph()

class ir_documentation_screenshot(osv.osv):
    _name = 'ir.documentation.screenshot'
    _description = 'Documentation Screenshot'
    _rec_name = 'reference'

    _columns = {
        'paragraph_id': fields.many2one('ir.documentation.paragraph', 'Paragraph', required=True, ondelete='cascade'),
        'user_id': fields.many2one('res.users', 'User', required=True, ondelete='cascade'),
        'view_id': fields.many2one('ir.ui.view', 'View', required=True, ondelete='cascade'),
        'field': fields.char('Field', size=100, help='This field will be visible in this screenshot.'),
        'reference': fields.char('Reference', size=256, required=True),
        'image': fields.binary('Image', filters=['*.png']),
    }
ir_documentation_screenshot()

class ir_documentation_menu(osv.osv):
    _name = 'ir.documentation.menu'
    _description = 'Documentation Menu'
    _rec_name = 'reference'

    _columns = {
        'paragraph_id': fields.many2one('ir.documentation.paragraph', 'Paragraph', required=True, ondelete='cascade'),
        'reference': fields.char('Reference', size=500, required=True),
        'menu_id': fields.many2one('ir.ui.menu', 'Menu'),
        'indent': fields.integer('Indent', required=True, help='Number of spaces of indent of the paragraph.'),
    }
ir_documentation_menu()

class ir_documentation_field(osv.osv):
    _name = 'ir.documentation.field'
    _description = 'Documentation Field'
    _rec_name = 'reference'

    _columns = {
        'paragraph_id': fields.many2one('ir.documentation.paragraph', 'Paragraph', required=True, ondelete='cascade'),
        'reference': fields.char('Reference', size=500, required=True),
        'field_id': fields.many2one('ir.model.fields', 'Field'),
        'indent': fields.integer('Indent', required=True, help='Number of spaces of indent of the paragraph.'),
        'help': fields.boolean('Show Help', help='If set, it will show help information associated with the field instead of the label of the field.'),
    }
ir_documentation_field()

class ir_documentation_view(osv.osv):
    _name = 'ir.documentation.view'
    _description = 'Documentation View'
    _rec_name = 'reference'

    _columns = {
        'paragraph_id': fields.many2one('ir.documentation.paragraph', 'Paragraph', required=True, ondelete='cascade'),
        'reference': fields.char('Reference', size=500, required=True),
        'view_id': fields.many2one('ir.ui.view', 'View'),
        'indent': fields.integer('Indent', required=True, help='Number of spaces of indent of the paragraph.'),
        'field': fields.char('Field', size=100, help='If set, the system will ensure this field is shown when creating the screenshot.'),
    }
ir_documentation_view()

class ir_documentation_file(osv.osv):
    _name = 'ir.documentation.file'
    _description = 'Documentation File'
    _rec_name = 'filename'
    _order = 'filename'

    _columns = {
        'data': fields.binary('Data', help='File content'),
        'filename' : fields.char('Filename', size=500, required=True),
        'user_id': fields.many2one('res.users', 'User', required=True, ondelete='cascade'),
    }

    def get(self, cr, uid, path, context):
        path = path.lstrip('/')
        ids = self.search(cr, uid, [('user_id','=',uid),('filename','=',path)], context=context)
        if not ids:
            return False
        file = self.browse(cr, uid, ids[0], context)
        return file.data

ir_documentation_file()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

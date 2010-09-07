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

src_chars = """àáäâÀÁÄÂèéëêÈÉËÊìíïîÌÍÏÎòóöôÒÓÖÔùúüûÙÚÜÛçñºª·¤ '"()/*-+?!&$[]{}@#`'^:;<>=~%\\""" 
src_chars = unicode( src_chars, 'utf-8' )
dst_chars = """aaaaAAAAeeeeEEEEiiiiIIIIooooOOOOuuuuUUUUcnoa_e______________________________"""
dst_chars = unicode( dst_chars, 'utf-8' )

def normalize(text):
	if isinstance( text, unicode ):
		text = text.encode('utf-8')
	return text

def unaccent(text):
    if isinstance( text, str ):
        text = unicode( text, 'utf-8' )
    output = text
    for c in xrange(len(src_chars)):
        output = output.replace( src_chars[c], dst_chars[c] )
    return output.strip('_').encode( 'utf-8' )

def stripped(text):
    return text.strip('\n').strip()

def paragraph_type(text):
    if text.startswith('===') and text.endswith('==='):
        return 'title'
    elif text.endswith('==='):
        return 'chapter'
    elif text.startswith('---') and text.endswith('---'):
        return 'section'
    elif text.endswith('---'):
        return 'subsection'
    else:
        return 'paragraph'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

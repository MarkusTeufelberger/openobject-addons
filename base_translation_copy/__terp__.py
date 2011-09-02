# -*- encoding: utf-8 -*-
##############################################################################
#
#    This module is copyright (C) 2011 Numérigraphe SARL. All Rights Reserved.
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

{
    'name' : 'Copy Translations to English',
    'version' : '0.1',
    'author' : u'Numérigraphe',
    'category' : 'Custom',
    'depends' : [],
    'description': """\
This module lets you copy all the translations of a language to English.

This is useful because English is the default language for all objects in
OpenERP, so when users work in any another language they will have to manage
translations to and from the English language.
When they don't, operations such as object copying or renaming will produce
unexpected behaviors because the English names are not updated.
To tackle this in an environment where English is not used by the users,
this module adds a wizard in Administration > Translations to let you copy
all the strings in one language to the English translations.""",
    'demo_xml' : [],
    'init_xml' : [],
    'update_xml' : ['copy_translations_wizard.xml'],
    'active': False,
    'installable': True,
    'license' : 'GPL-3',
}


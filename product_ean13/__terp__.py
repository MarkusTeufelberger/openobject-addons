# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Ana Juaristi (http://openerpsite.com) All Rights Reserved.
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

{
    "name" : "Products Sequence",
    "version" : "0.1",
    "author" : "Ana Juaristi",
    "website" : "www.openerpsite.com",
    "category" : "Localisation/Europe",
    "description": """
This module:
  * Adds a wizard on product form to generate valid EAN13 product codes.
  * By default EAN13 will be generated with spanish country code (84) and 11111 company code. 
Each company should change this values on administration/sequences to addecuate to his country and company code.

Este módulo:
  * Añade un asistente al producto para crear un código EAN13 con formato válido.
  * Por defecto, el código EAN13 será generado con la secuencia de país 84 y el código de empresa 1111.
Cada compañía deberá adecuar estos valores por defecto a los de su país y empresa en Administración/Personalización/Secuencias.
La secuencia de productos por defecto se inicia en 1 (y relleno de 5 dígitos tal como recomienda AECOC) 
    """,
    "license" : "GPL-3",
    "depends" : ["base","product",],
    "init_xml" : [],
    "update_xml" : [
        "product_seq_sequence.xml",
        "product_seq_wizard.xml"
        ],
    "active": False,
    "installable": True
}





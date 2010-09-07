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

{
    "name" : "Date in SO lines",
    "description":"""This module allows to set planned execution date in Sale order
    When the So is confirmed the delay is automtically computed this way you do not have to use 
    day for computing Delivery date of generated picking. If a date is set on the SO, it will automatically be taken in so line, if not it will recompute a date based on the product customer lead time !!!Warning this module overrite the so line product_id_change function  and add a parameters in signature. If there alerady is a module that does the same they will conflict""",
    "version" : "1.0",
    "depends" : [
                    "base",
                    "sale",
                ],
    "author" : "Camptocamp SA",
    "init_xml" : [],
    "update_xml": [
                        "sale_order_line_view.xml",
                   ],
    "installable" : True,
    "active" : False,
}
# -*- coding: utf-8 -*-
# author: ChriCar Beteiligungs- und Beratungs- GmbH
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
{
	"name" : "ChriCar unique View ID",
	"version" : "0.2",
	"author" : "Network Gulf IT - India",
	"website" : "http://www.chricar.at/ChriCar/index.html",
	"description": """
This module is funded by
ChriCar Beteiligungs- und Beratungs- GmbH
http://www.chricar.at/ChriCar/index.html

Developed by
Network Gulf IT - India
http://www.networkgulf.com/

usage: get_id('your_view_name',param1,param2,param3,param4)
this function will always return the SAME unique id for a 
certain combination of parameters for a view.

Hint 1: you do not need this function if the unique id can easily be 
calculated during the grouping. Example
- easy: group by product_id
- more complex: group by account_id, period_id
- very complex: group by account_id, period_id, currency_id

Hint 2: for large tables (100000 rec)  
performance gain of factor 10x and more
split the grouping operation and the get_id into 2 views

slow:
select get_id(tablename,param1,param2,...), param1, param2, ... sum(field1), ...
from
group by get_id(tablename,param1,param2,...) ,param1,param2,...

fast:
1) view1: 
select ....
from
group by param1,param2,...
2) view 2
select get_id('view1',param1,param2,...),* from view1;
(no group by here)
""",
	"depends" : ["base"],
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [],
	"active": False,
	"installable": True
}

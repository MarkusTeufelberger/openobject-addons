#!/usr/bin/python
# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
import sys
sys.path.append('..')

import etl


fileconnector_partner=etl.connector.localfile('input/partner.csv')
fileconnector_partner2=etl.connector.localfile('input/partner2.csv')

in1 = etl.component.input.csv_in(fileconnector_partner,name='Partner Data')
in2 = etl.component.input.csv_in(fileconnector_partner2,name='Partner Data2')
diff1 = etl.component.transform.diff(['id'])

log_1 = etl.component.transform.logger_bloc(name="Original Data")
log_2 = etl.component.transform.logger_bloc(name="Modified Data")

log1 = etl.component.transform.logger(name="Log Same")
log2 = etl.component.transform.logger(name="Log Add")
log3 = etl.component.transform.logger(name="Log Remove")
log4 = etl.component.transform.logger(name="Log Update")

fileconnector_output=etl.connector.localfile('output/test2_add.csv', 'w+')
csv_out1 = etl.component.output.csv_out(fileconnector_output,name='Output')

etl.transition(in1, log_1)
etl.transition(in2, log_2)

etl.transition(in1, diff1, channel_destination='original')
etl.transition(in2, diff1, channel_destination='modified')

etl.transition(diff1, log1, channel_source="same")
etl.transition(diff1, log3, channel_source="remove")
etl.transition(diff1, log2, channel_source="add")
etl.transition(diff1, csv_out1, channel_source="add")
etl.transition(diff1, log4, channel_source="update")

job = etl.job([in1,in2,log_1,log_2,diff1,log1,log2,log3,log4,csv_out1])
print job
job.run()
print job.get_statitic_info()

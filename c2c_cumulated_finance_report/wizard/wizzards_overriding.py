# -*- encoding: utf-8 -*-
#  wizzards_overriding.py
#  c2c_cumulated_finance_report
#  Created by Nicolas Bessi
#  Copyright (c) 2010 CamptoCamp. All rights reserved.
####################################################################
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.


##we ovverride the states class properties of the wizards that call the reports.
## it is more dry this way
import account
account.wizard.wizard_general_ledger_report.wizard_report.states['report']['result'] = {'type':'print', 'report':'account.general.ledger_cumulated', 'state':'end'}
account.wizard.wizard_general_ledger_report.wizard_report.states['report_landscape']['result'] = {'type':'print', 'report':'account.general.ledger_landscape_cumulated', 'state':'end'}  
account.wizard.wizard_third_party_ledger.wizard_report.states['report']['result'] = {'type':'print', 'report':'account.third_party_ledger_cumulated', 'state':'end'}
account.wizard.wizard_third_party_ledger.wizard_report.states['report_other']['result'] = {'type':'print', 'report':'account.third_party_ledger_other_cumulated', 'state':'end'}

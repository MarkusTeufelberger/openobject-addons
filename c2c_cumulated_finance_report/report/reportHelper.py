# -*- encoding: utf-8 -*-
#  reportsHelpers.py
#  Created by Nicolas Bessi 
#  Copyright (c) 2009 CamptoCamp. All rights reserved.
##############################################################################
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
import re
from mx import DateTime
import operator

class ReportHelper(object):
    """Class should be integrated inside reporting tool of the core"""
    
    def __init__(self, pool, cr, uid):
        self.pool = pool
        self.cr = cr
        self.uid = uid
        self.totdict = {}
        self.memoizedict = {}
##Total computation helpers        
    def incr_total(self, column, val) :
        """Initialize a increment total in the store by his key and the value in enter"""
        if self.totdict.has_key(column) :
            self.totdict[column] =  self.totdict[column]+val
        else :
            self.totdict[column] = val
            
    def reset_total(self, column) :
        "reset the total in the store by his key"
        self.totdict[column] =  0.0
        
    def get_total(self, column) :
        "return the total in the total store by his key"
        return self.totdict[column] or 0.0
## Memoizer helpers      
    def memoize(self, key, val):
        """Put a value in the store indentified by his key"""
        self.memoizedict[key] = val
        
    def remember(self, key):
        "Return the value in the store by his key"
        return self.memoizedict.get(key)
        
    def forget(self):
        self.memoizedict = {}
# Formatting helpers        
    def comma_me(self,amount):
        """Tihs will return a formatted float"""
        if  type(amount) is float :
          amount = str('%.2f'%amount)
        else :
          amount = str(amount)
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>'\g<2>", amount)
        if orig == new:
          return new
        else:
          return self.comma_me(new)
          
    def _ellipsis(self, string, maxlen=100, ellipsis = '...'):
      ellipsis = ellipsis or ''
      try:
          return string[:maxlen - len(ellipsis) ] + (ellipsis, '')[len(string) < maxlen]
      except Exception, e:
          return False
    def strip_name(self, name, maxlen=50):
        return self._ellipsis(name, maxlen, '...')
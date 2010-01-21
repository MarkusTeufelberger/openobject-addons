#########################################################################
#   #####     #   #        # ####  ###     ###  #   #   ##  ###   #     #
#   #   #   #  #   #      #  #     #  #    #    # # #  #  #  #    #     #
#   ####    #   #   #    #   ###   ###     ###  #   #  #  #  #    #     #
#   #        # #    # # #    #     # #     #    #   #  ####  #    #     #
#   #         #     #  #     ####  #  #    ###  #   #  #  # ###   ####  #
# Copyright (C) 2009  Sharoon Thomas OpenLabs                           #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from osv import osv,fields
import string,random
from tools.translate import _

class res_users(osv.osv):
    _inherit = "res.users"
    
    def makePassword(self,minlength=5,maxlength=8):
          length=random.randint(minlength,maxlength)
          letters=string.ascii_letters+string.digits # alphanumeric, upper and lowercase
          return ''.join([random.choice(letters) for _ in range(length)])
      
    def reset_password(self,cr,uid,id):
        #generate random password
        new_password = self.makePassword()
        self.write(cr,uid,id,{'password':new_password})
        #select template
        ir_records = self.pool.get('ir.model.data').search(cr,uid,[('module','=','ol_password_reset'),('name','=','reset_template')])
        if ir_records and len(ir_records)==1:
            ir_rec = self.pool.get('ir.model.data').browse(cr,uid,ir_records[0])
            template_id = ir_rec.res_id
            self.pool.get('poweremail.templates').generate_mail(cr,uid,template_id,[id])
            return True
        else:
            raise osv.except_osv(
                _('Error'),
                _("Could not fetch template. Please upgrade module"))
        #send password
    def send_password(self,cr,uid,id):
        #select template
        ir_records = self.pool.get('ir.model.data').search(cr,uid,[('module','=','ol_password_reset'),('name','=','send_template')])
        if ir_records and len(ir_records)==1:
            ir_rec = self.pool.get('ir.model.data').browse(cr,uid,ir_records[0])
            template_id = ir_rec.res_id
            self.pool.get('poweremail.templates').generate_mail(cr,uid,template_id,[id])
            return True
        else:
            raise osv.except_osv(
                _('Error'),
                _("Could not fetch template. Please upgrade module"))
        #send password 
        
res_users()
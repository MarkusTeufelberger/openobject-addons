# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi & Guewen Baconnier. Copyright Camptocamp SA
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

import ftplib
import paramiko

from osv import fields, osv
from tools.translate import _

class ResCompany(osv.osv):
    """override company to add product price computation"""
    _inherit = "res.company"
    _columns = {
        'ftp_active':fields.boolean('Extra media support', help='The medias supported by the Magento API are "jpg, gif, png". For other file types, activate the FTP/SFTP support.'),
        'ftp_server':fields.char('FTP server url', size=256),
        'ftp_cwd':fields.char('FTP image path', size=256),
        'ftp_login':fields.char('FTP Login', size=256),
        'ftp_password':fields.char('FTP Password', size=256),
        'ftp_tsl':fields.boolean('FTP TSL'),
        'ftp_ssh':fields.boolean('SFTP'),
        
        'local_media_repository':fields.char(
                        'Path to OpenERP Media folder', 
                        size=256, 
                        required=True,
                        help='Local mounted path on OpenERP server. Put all your medias files into that folder.'
                    ),
    }    
    
    def ftp_connect(self, cr, uid, company_id, context=None):
        if not context:
            context = {}

        ftp = None
        company = self.browse(cr, uid, company_id, context)
        is_ssh = company.ftp_ssh
        try:
            if is_ssh:
                transport = paramiko.Transport((company.ftp_server, 22))
                transport.connect(username=company.ftp_login, 
                                  password=company.ftp_password)
                ftp = paramiko.SFTPClient.from_transport(transport)
                if company.ftp_cwd :
                    ftp.chdir(company.ftp_cwd)                                    
            else:
                if company.ftp_tsl :
                    ftp = ftplib.FTP_TLS(company.ftp_server)
                else:
                    ftp = ftplib.FTP(company.ftp_server)
                ftp.login(company.ftp_login, 
                          company.ftp_password)
                if company.ftp_cwd:
                    ftp.cwd(company.ftp_cwd)
        except Exception, e:
            raise Exception(_('Could not establish connection with ftp/sftp server: ') + str(e))        
        return {'ftp_object': ftp, 'is_ssh': is_ssh}
    
ResCompany()

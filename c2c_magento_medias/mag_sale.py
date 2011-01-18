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
from osv import osv, fields
import netsvc
from tools.translate import _
import string
#from datetime import datetime
import time
from  magentoerpconnect import magerp_osv
import ftplib
import paramiko
class SaleShop(magerp_osv.magerp_osv):
    _inherit = "sale.shop"
    def export_images(self, cr, uid, ids, context=None):
        """ Override the export images function to add the connection to the ftp/sftp server """
        if not context:
            context = {}
        
        ftp = None
        company_obj = self.pool.get('res.company')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        company = user.company_id
        
        context['base_path'] = company.local_media_repository
        
        if company.ftp_active:
            connect = company_obj.ftp_connect(cr, uid, company.id, context)
            ftp = connect['ftp_object']
            context['ftp'] = ftp
            context['is_ssh'] = connect['is_ssh']
            
        res = super(SaleShop, self).export_images(cr, uid, ids, context)
        
        if company.ftp_active:        
            ftp.close()
            ftp = None
        return res
SaleShop()

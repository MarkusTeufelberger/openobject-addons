# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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
    'name' : 'c2c_magento_medias',
    'version' : '1',
    'depends' : ['base', 'product','magentoerpconnect'],
    'author' : 'Camptocamp',
    'description': """Extend the product image capabilities for Magento :
 - Attach others media than jpg, gif, png as pdf, flash etc. and export them to a FTP/SFTP server allowing Magento to handle them.
 - Wizard to add simply images or other medias 
 - Unlink images on OpenERP delete them on Magento
 
Configure the "Path to OpenERP media folder" on the company, that is the folder where all your images and other will be stored.
The images to create on Magento must be of type "link" and the filename must not contains the full path of the file.
OpenERP will search for them in the configured path.
You can use the wizard "Load a media" on the product to copy the media directly in the "OpenERP media folder".

If you want to attach pdf, flash or other files to products on Magento, you have to activate the "Extra media support" on the company and configure the FTP/SFTP.
Needs modification on the Magento side to handle the medias sent on the ftp repository.
""",
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [
                   'company_view.xml', 
                   'wizard/load_product_media_view.xml',
                   'product_image_view.xml',
                  ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

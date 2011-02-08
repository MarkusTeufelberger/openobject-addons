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

import os
import base64, urllib
import ftplib
import mag_sale
import netsvc
import mimetypes
import errno
import paramiko

from magentoerpconnect import magerp_osv
from osv import fields, osv
from tools.translate import _

class ProductImages(magerp_osv.magerp_osv):
    "Products Image gallery"
    _inherit = "product.images"

    BASE_IMAGE_TYPES = ['.png', '.jpg', '.jpeg', '.gif']

    def get_image(self, cursor, uid, id):
        user = self.pool.get('res.users').browse(cursor, uid, uid)
        company = user.company_id
        each = self.read(cursor, uid, id, ['link', 'filename', 'image'])
        img = None
        if each['link']:
            if each['filename']:
                file, ext = os.path.splitext(each['filename'])
                if ext.lower() not in self.BASE_IMAGE_TYPES:
                    return False
                try :
                    (filename, header) = urllib.urlretrieve(os.path.join(company.local_media_repository, each['filename']))
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    return False #Volunteer silent path in order to be able to access form view
        else:
            img = each['image']
        return img


    def update_remote_images(self, cr, uid, ids, context=None):
        """Deal with image that are not standard image file like flash, etc...
        Errors during sync will set the sync_status to False, Success to True."""
        if context is None:
            raise 'not context'
        logger = netsvc.Logger()
        conn = context.get('conn_obj', False)
        if not conn:
            return False

        user = self.pool.get('res.users').browse(cr, uid, uid)
        company = user.company_id

        # Add image that had not passed the last sync if there are some
        ids_to_add=self.pool.get('product.images').search(cr,uid,[('sync_status','=',False)])
        ids=list(set(ids+ids_to_add))

        def detect_types(image):
            types = []
            if image.small_image:
                types.append('small_image')
            if image.base_image:
                types.append('image')
            if image.thumbnail:
                types.append('thumbnail')
            return types

        def sftp_base_push(ftp, base_path, ftp_path, filename):
            localpath = os.path.join(base_path, filename)
            remotepath = os.path.join(ftp_path, filename)
            try :
                ftp.put(localpath, remotepath)
            except Exception, e:
                raise Exception('Can not push file '+ filename +' '+str(e))

        def ftp_base_push(ftp, base_path, ftp_path, filename):
            try :
                filehandel =  open(os.path.join(base_path, filename), "rb")
            except Exception, e:
                raise Exception('Can not open file '+ filename +' '+str(e))
            try :
                ftp.storbinary("STOR " + os.path.join(ftp_path, filename), filehandel)
            except Exception, e:
                raise Exception('Can not push file '+ filename +' '+str(e))

        def sftp_mkdir(ftp, filename):
            l1 = filename[0]
            l2 = filename[1]
            path = os.path.join(l1,l2)
            try:
                ftp.stat(l1)
            except IOError, e:
                if e.errno == errno.ENOENT:
                    ftp.mkdir(l1)
                else :
                    raise e
            try:
                ftp.stat(path)
            except IOError, e:
                if e.errno == errno.ENOENT:
                    ftp.mkdir(path)
                else :
                    raise e
            return path
            #FTPLIST = context['FTPLIST]
            # if l1 in FTPLIST :
            #     if not l2 in FTPLIST :
            #         FTP.mkdir(os.path.join(l1,l2))
            #         FTPLIST[l1].append(l2)
            # else :
            #     FTP.mkdir(l1)
            #     FTP.mkdir(os.path.join(l1,l2))
            #     FTPLIST[l1] = [l2]
            #

        def ftp_mkdir(ftp, filename):
            l1 = filename[0]
            l2 = filename[1]
            path = os.path.join(l1,l2)
            #non optimised version
            if not l1 in ftp.nlst() :
                ftp.mkd(l1)
                ftp.mkd(path)
                return path
            if not l2 in ftp.nlst(l1):
                ftp.mkd(path)
                return path
            return path

            #FTPLIST = context['FTPLIST]
            # if l1 in FTPLIST :
            #     if not l2 in FTPLIST :
            #         FTP.mkd(os.path.join(l1,l2))
            #         FTPLIST[l1].append(l2)
            # else :
            #     FTP.mkd(l1)
            #     FTP.mkd(os.path.join(l1,l2))
            #     FTPLIST[l1] = [l2]

        def is_ftp_media(cr, uid, image):
            if not image.filename:
                return False
            file, ext = os.path.splitext(image.filename)
            if ext.lower() in self.BASE_IMAGE_TYPES:
                return False
            return True

        def ftp_push(cr, uid, image, ftp, base_path, is_ssh):
            filename = image.filename
            if is_ssh:
                ftp_path = sftp_mkdir(ftp, filename)
                sftp_base_push(ftp, base_path, ftp_path, filename)
            else:
                ftp_path = ftp_mkdir(ftp, filename)
                ftp_base_push(ftp, base_path, ftp_path, filename)

            self.write(cr, uid, image.id, {'mage_file': os.path.join(ftp_path, filename)})
            return True

        def create_image(cr, uid, image):
            result = False
            content = self.get_image(cr, uid, image.id)
            
            if content:
                result = conn.call('catalog_product_attribute_media.create',
                      [image.product_id.magento_sku,
                       {'file':{
                                # send file name without extension
                                'name': os.path.splitext(os.path.basename(image.filename))[0],
                                'content': content,
                                'mime': image.filename and mimetypes.guess_type(image.filename)[0] or 'image/jpeg',
                                }
                       }
                       ])
                self.write(cr, uid, image.id, {'mage_file':result,'sync_status':True})
                cr.commit()
            else:
                logger.notifyChannel('Medias creation', netsvc.LOG_ERROR, "The content of the file: %s is empty on product %s (sku : %s)" % (each.filename, each.product_id.name, each.product_id.magento_sku))
            return result

        def update_image(content, image):
            result = conn.call('catalog_product_attribute_media.update',
                               [image.product_id.magento_sku,
                                content,
                                {'label':image.name,
                                 'exclude':image.exclude,
                                 'types':detect_types(image),
                                }
                               ])
            return result

        for each in self.browse(cr, uid, ids, context=context):
            if not each.product_id.magento_exportable:
                continue
            
            # only manage file which are links, because magento needs the mimetype and we don't know it on non-linked products
            if not each.link:
                continue

            ftp_media = is_ftp_media(cr, uid, each)

            if each.mage_file: #If update
                if ftp_media:
                    if company.ftp_active:
                        result = ftp_push(cr, uid, each, context['ftp'], context['base_path'], context['is_ssh'])
                else:
                    result = update_image(each.mage_file, each)
                if result:
                    logger.notifyChannel('Medias update', netsvc.LOG_INFO, "Product %s's image updated: %s" % (each.product_id.name, each.product_id.magento_sku))
            else:
                if each.product_id.magento_sku:
                    logger.notifyChannel('ext synchro', netsvc.LOG_INFO, "Sending %s's image: %s" % (each.product_id.name, each.product_id.magento_sku))
                    if ftp_media:
                        if company.ftp_active:
                            result = ftp_push(cr, uid, each, context['ftp'], context['base_path'], context['is_ssh'])
                        else:
                            logger.notifyChannel('Medias update', netsvc.LOG_INFO, "Skipping product %s's media : %s on sku : %s because the ftp is not active." % (each.product_id.name, each.filename, each.product_id.magento_sku))
                    else:
                        try:
                            result = create_image(cr, uid, each)
                            result = update_image(result, each)
                        # removed "failsafe" option because if we do that, all files in error and skipped will
                        # never be updated
                        except Exception, e:
                            logger = netsvc.Logger()
                            logger.notifyChannel('Medias update', netsvc.LOG_ERROR, "Error during Magento image creation: %s" % (e))
                            self.write(cr,uid,each.id,{'sync_status':False})
                            continue

        return True

    def create(self, cr, uid, vals, context=None):
        """Prevent the creation of other files than images when the ftp is not active."""
        if context is None:
            context = {}
	        
        user = self.pool.get('res.users').browse(cr, uid, uid)
        company = user.company_id

        if vals['link']:
            if vals['filename']:
                file, ext = os.path.splitext(vals['filename'])
            
            if not company.ftp_active and ext not in self.BASE_IMAGE_TYPES:
                raise osv.except_osv(_("Load media"), _("Impossible to load an other type of media than \"%s\" when the extra media support is not activated on the company (%s)." % (', '.join(self.BASE_IMAGE_TYPES), vals['filename'])))

        return super(ProductImages, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        """ Delete image on Magento before deleting it on OpenERP """

        def sftp_base_unlink(sftp, file):
            """ Unlink for SFTP """
            try:
                sftp.unlink(file)
            except Exception, e:
                raise Exception('Can not unlink file '+ file +' '+str(e))

        def ftp_base_unlink(ftp, file):
            """ Unlink for FTP """
            try:
                ftp.delete(file)
            except Exception, e:
                raise Exception('Can not unlink file '+ file +' '+str(e))

        if context is None:
            context = {}

        logger = netsvc.Logger()
        shop_obj = self.pool.get('sale.shop')
        product_obj = self.pool.get('product.product')
        company_obj = self.pool.get('res.company')

        # get all magento shops
        shops_ids = shop_obj.search(cr, uid, [('magento_shop', '=', True)])

        user = self.pool.get('res.users').browse(cr, uid, uid)
        company = user.company_id

        for image in self.browse(cr, uid, ids, context):
            # mage_file is the name of the file on magento
            if not image.mage_file:
                continue

            file, ext = os.path.splitext(image.filename)
            # image are managed by magento api, other medias by ftp
            if ext.lower() in self.BASE_IMAGE_TYPES:
                # we'll delete the image in each magento shop
                for shop in shop_obj.browse(cr, uid, shops_ids, context):
                    # search if the product exists on that shop
                    # and get the id of the product in magento
                    magento_product_id = product_obj.oeid_to_extid(cr,
                                                                   uid,
                                                                   image.product_id.id,
                                                                   shop.referential_id.id,
                                                                   context)
                    if not magento_product_id:
                        continue

                    # create connection with magento
                    conn = shop_obj.external_connection(cr, uid, shop.referential_id)
                    if not conn:
                        raise osv.except_osv(_('Delete image'),
                                             _("Could not establish connection with Magento."))

                    # get image list on magento for the product
                    mag_images = conn.call('catalog_product_attribute_media.list',
                                           [
                                            magento_product_id,
                                           ])
                    # check if the image still exists on Magento before drop it
                    for mag_image in mag_images:
                        if mag_image['file'] == image.mage_file:
                            # delete image on Magento
                            conn.call('catalog_product_attribute_media.remove',
                                      [
                                       magento_product_id,
                                       image.mage_file,
                                      ])
                            logger.notifyChannel('ext synchro',
                                                 netsvc.LOG_INFO,
                                                 "Deleted %s's image: %s" % (image.product_id.name, image.name))
                            break
            else:
                if company.ftp_active:
                    connect = company_obj.ftp_connect(cr, uid, company.id, context)
                    ftp = connect['ftp_object']
                    is_ssh = connect['is_ssh']
                    if is_ssh:
                        sftp_base_unlink(ftp, image.mage_file)
                    else:
                        ftp_base_unlink(ftp, image.mage_file)
                    logger.notifyChannel('ext synchro',
                                         netsvc.LOG_INFO,
                                         "Deleted %s's media on FTP/SFTP: %s" % (image.product_id.name, image.name))
                    ftp.close()
                    ftp = None

        return super(ProductImages, self).unlink(cr, uid, ids, context)


ProductImages()

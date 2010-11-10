# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright Camptocamp SA
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

from osv import fields, osv, orm
from tools import ustr
from tools.translate import _
import StringIO
import base64
import binascii
import csv
import netsvc
import pdb
import pooler
import pprint
import tools
import wizard

try:
    import pyExcelerator as xl
    
    class XlsDoc(xl.CompoundDoc.XlsDoc):
        def saveAsStream(self, ostream, stream):
            # 1. Align stream on 0x1000 boundary (and therefore on sector boundary)
            padding = '\x00' * (0x1000 - (len(stream) % 0x1000))
            self.book_stream_len = len(stream) + len(padding)

            self.__build_directory()
            self.__build_sat()
            self.__build_header()

            ostream.write(self.header)
            ostream.write(self.packed_MSAT_1st)
            ostream.write(stream)
            ostream.write(padding)
            ostream.write(self.packed_MSAT_2nd)
            ostream.write(self.packed_SAT)
            ostream.write(self.dir_stream)

    class Workbook(xl.Workbook):
        def save(self, stream):
            doc = XlsDoc()
            doc.saveAsStream(stream, self.get_biff_data())    
    
except :
    print 'pyExcelerator Python module not installed'

class c2c_export_pricelist(osv.osv_memory):
    """Export Pricelist"""
    _name = 'c2c.export.pricelist'
    _description = 'Export Pricelist'
    _columns = {
        'data': fields.binary('File', readonly=True),
        'name': fields.char('Filename', 16, readonly=True),
        'format': fields.selection([('xls','XLS'),('csv','CSV'),], 'Save As:')
    }
    _defaults = {
        'format': lambda *a: 'csv'         
    }

    def export_data(self,cr,uid,ids,context=None):
        excel_enabled = True
        try:
            mydoc=Workbook()
        except:
            excel_enabled = False
            
        if excel_enabled:
            #Add a worksheet
            mysheet=mydoc.add_sheet("Pricelist")
            #write headers
            header_font=xl.Font() #make a font object
            header_font.bold=True
            #font needs to be style actually
            header_style = xl.XFStyle(); header_style.font = header_font

        product_obj = pooler.get_pool(cr.dbname).get('product.product')
        product = product_obj.browse(cr, uid, ids)
        
        wiz = self.browse(cr, uid ,ids)[0]
        
        if wiz.format == 'xls':
            if not excel_enabled:
                raise osv.except_osv(_("Export Pricelist error"), _("Impossible to export the pricelist as Excel file. Please install PyExcelerator to enable this function."))
            
            filename = 'PriceList.xls'
        else:
            filename = 'PriceList.csv'
                
        keys=['','']
        file_csv=StringIO.StringIO()
        keys=['EAN13', 'Supplier', 'Supplier Delay', 'Supplier Min. Qty', 'Supplier Code', 'Supplier Name', 'Quantity', 'Price']
        #Encode keys        
        key_values = [tools.ustr(k).encode('utf-8') for k in keys]
        
        if excel_enabled:        
            for col, value in enumerate(key_values):
                mysheet.write(0,col,value,header_style)
            
        writer=csv.writer(file_csv, delimiter= ';', lineterminator='\r\n')
        writer.writerow(keys)

        prod_ids = product_obj.search(cr, uid, [('ean13', '!=', False)])
        for prod in product_obj.browse(cr, uid, prod_ids):
            row_lst = []
            row = []
            if prod.seller_ids:
               for seller in prod.seller_ids:
                    for supplier in seller.pricelist_ids:
                        row.append(prod.ean13 or ' ')
                        row.append(seller.name.name or '')
                        row.append(seller.delay or ' ')
                        row.append(seller.qty or ' ')
                        row.append(seller.product_name or ' ')
                        row.append(seller.product_code or ' ')
                        row.append(supplier.min_quantity or ' ')
                        row.append(supplier.price or ' ')
                        row_lst.append(row)
                        writer.writerow(row)
            else:
                row.append(prod.ean13 or ' ')
                row.append('-')
                row.append('')
                row.append('')
                row.append('')
                row.append('')
                row.append('')
                row.append('')
                row_lst.append(row)
                writer.writerow(row)
                        
        if excel_enabled:                          
            for row_num,row_values in enumerate(row_lst):
                row_num+=1 #start at row 1
                row_values = [tools.ustr(x).encode('utf-8') for x in row_values]
                for col,value in enumerate(row_values):
                    #normal row
                    mysheet.write(row_num,col,value)

        if wiz.format == 'xls':
            file_xls=StringIO.StringIO()
            out=mydoc.save(file_xls)
            out=base64.encodestring(file_xls.getvalue())
        else:
            out = base64.encodestring(file_csv.getvalue())
        result = self.write(cr, uid, ids, {'data':out, 'name': filename}, context=context)
        return result
        
c2c_export_pricelist()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

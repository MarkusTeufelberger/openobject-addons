{
	"name" : "Procurement Cheapest Supplier",
	"version" : "0.1",
	"description" : """This module selects the cheapest supplier for a product when purchase orders are created from procurements. By default OpenERP will select the partner with lowest sequence number.""",
	"author" : "NaN for Trod y Avia, S.L.",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 
		'mrp',
		'nan_product_supplier_info_extended',
	],
	"category" : "Custom Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [ 
	],
	"active": False,
	"installable": True
}

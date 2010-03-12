{
	"name" : "Production Lot Cost",
	"version" : "0.1",
	"description" : """This module adds cost information to production lots.""",
	"author" : "NaN for Guinama (www.guinama.com)",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 
		'stock',
		'mrp',
		'purchase',
	],
	"category" : "Custom Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [ 
		'stock_view.xml',
	],
	"active": False,
	"installable": True
}

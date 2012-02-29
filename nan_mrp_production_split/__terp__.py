# encoding: utf-8
{
	"name" : "Production Split",
	"version" : "0.1",
	"description" : """This module adds a new wizard that allows splitting a production order into two.
    
Developed for Trod y Avia, S.L.""",
	"author" : "NaN·tic",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 
		'mrp',
	],
	"category" : "Custom Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [ 
		'mrp_view.xml',
	],
	"active": False,
	"installable": True
}

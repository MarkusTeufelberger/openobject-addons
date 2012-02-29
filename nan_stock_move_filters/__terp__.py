# encoding: utf-8
{
	"name" : "Stock Move Filters",
	"version" : "0.1",
	"description" : """This module adds filters to stock moves so only available locations, products and lots are shown in searches, easing the selection of the appropiate ones to the user.
	
This module provides a useful infrastructure for specific filters to be implemented in new modules.

Developed for Trod y Avia, S.L.""",
	"author" : "NaN·tic",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 
		'stock',
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

{
	"name" : "Product Pack",
	"version" : "0.1",
	"description" : """Allows configuring products as a collection of other products. If such a product is added in a sale order, all the products of the pack will be added automatically (when storing the order) as children of the pack product.""",
	"author" : "NaN",
	"website" : "http://www.NaN-tic.com",
	"depends" : [ 
		'sale'
	], 
	"category" : "Custom Modules",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [ 'pack_view.xml' ],
	"active": False,
	"installable": True
}

.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

||| : after : product.el_campo_f_product_field_product_category_sequence |||

En la sección "Propiedades de contabilidad" podemos definir ciertos datos contables que se utilizarán en caso que el producto no los tenga establecidos. Esto significa que serán los valores por defecto de los productos de esa categoría.

**/// f: account.field_product_category_property_account_income_categ ///**
  Este campo sirve para anotar el código de cuenta financiera de ingresos a la que se associan los productos de esta categoria. De esta forma, se creará la línea del asiento contable de forma automática a la cuenta deseada.

**/// f: account.field_product_category_property_account_income_categ ///**
  Este campo sirve para anotar el código de cuenta financiera de gastos a la que se associan los procutos de esta categoria. De esta forma, se creará la línea del asiento contable de forma automática a la cuenta deseada.
		

||| : after : product.f_product_field_product_packaging_name |||

Contabilidad
------------

Algunos datos contables también pueden gestionarse en la ficha de producto:

/// v : product.product_normal_form_view :taxes_id ///

/// f:account.field_product_template_property_account_income ///	
  Este campo sirve para anotar el código de cuenta financiera de ingresos a la que se associa el producto. De esta forma, se creará la línea del asiento contable de forma automática a la cuenta deseada.

/// f:account.field_product_template_property_account_expense ///
  Este campo sirve para anotar el código de cuenta financiera de gastos a la que se associa el producto. De esta forma, se creará la línea del asiento contable de forma automática a la cuenta deseada.

/// f:account.field_product_template_taxes_id ///
  Aquí nos permite añadir diferentes impuestos relacionados con la venta del producto. Los campos que nos muestra son: /// f:account.field_account_tax_name ///, /// f:account.field_account_tax_price_include /// y /// f:account.field_account_tax_description ///


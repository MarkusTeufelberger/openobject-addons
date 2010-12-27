.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

---------
Productos
---------

Descripción
===========

Este módulo, nos habilita OpenERP para gestionar productos con sus respectivas categorias, listas de precios, variantes de producto, etc... A continuación describiremos más en detalle cada una de las funcionalidades.

Podremos ver que nos ha aparecido una nueva funcionalidad en el menú principal. En este caso 'Productos'.

Configuración
=============
	
Categorías de productos
-----------------------

Al entrar en /// m: product.menu_product_category_action_form /// podremos ver la lista de categorías que existen. Podremos filtrar el listado según su /// f : product.field_product_category_name ///  o según su /// f : product.field_product_category_parent_id ///.

Para crear una nueva categoría basta con clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

/// v : product.product_category_form_view ///

**/// f : product.field_product_category_name ///** 

En esta ventana, en el campo /// f : product.field_product_category_name /// introduciremos el nombre de la categoría que queramos crear. Hay que tener en cuenta que este nombre puede ser traducido, es decir, que podemos asignarle el nombre según el idioma que tengamos escogido.

**/// f : product.field_product_category_parent_id ///**

El campo /// f : product.field_product_category_parent_id /// especifica la categoría padre de la que estamos creando. Si la categoría que estamos creando no tiene categoría padre, lo podemos dejar en blanco.

**///  f : product.field_product_category_sequence ///**

El campo ///  f : product.field_product_category_sequence /// se utiliza para ordenar las categorías. Es decir, para cuando nos listan todas las categorías, nos las muestran según una secuencia que hemos determinado nosotros. 

Empaquetado
-----------

En esta opción podremos ver y crear las formas de empaquetado de que disponemos. Podremos filtrar el listado según su /// f :base.field_ir_ui_view_name /// o según su /// f :base.field_ir_ui_view_type ///

Para crear un nuevo empaquetado basta con clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

/// v :product.product_ul_form_view ///

**/// f :base.field_ir_ui_view_name ///** 

En esta ventana, en el campo /// f :base.field_ir_ui_view_name /// introduciremos el nombre del empaquetado que queramos crear. Hay que tener en cuenta que este nombre puede ser traducido, es decir, que podemos asignarle el nombre según el idioma que tengamos escogido.

**/// f : base.field_ir_ui_view_type ///**

El campo /// f :base.field_ir_ui_view_type  /// especifica el tipo de empaquetado que estamos definiendo. 

Unidades de medida
------------------

En este apartado tenemos dos funcionalidades:

A) Categorías de unidades de medida

	Aquí es donde definimos las categorías de unidades de medida (Volumen, peso, longitud,...)

	Para crear una nueva categoria basta con clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

	/// v :product.product_uom_categ_form_view ///

	Solo podremos indicar la Categoría en el campo /// f :base.field_ir_ui_view_name ///
	
..	_`unidad de medida`:

#) Unidades de medida

	Aquí definiremos las unidades de medida de cada categoría.

	Para crear una nueva unidad de medida basta con clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

	/// v :product.product_uom_form_view ///

	En esta ventana disponemos de los campos /// f:product.field_product_uom_name ///, /// f:product.field_product_uom_category_id ///, /// f:product.field_product_uom_factor ///, /// f:product.field_product_uom_factor_inv ///, /// f:product.field_product_uom_rounding /// y /// f:product.field_product_uom_active /// 

	I. **/// f :product.field_product_uom_name ///**
		Este campo se utiliza para dar el nombre a la unidad de medida

	#. **/// f: product.field_product_uom_category_id ///**
		Este campo indica la categoria a la que pertenece la unidad que estamos definiendo

	#. **/// f:product.field_product_uom_factor ///**
		Este campo indica el factor de conversión sobre la unidad base. Es decir que teniendo en cuenta que la unidad base tiene una /// f:product.field_product_uom_factor /// de 1.0, si la nueva unidad es por ejemplo 1 décima parte de la unidad base, el valor que tendría /// f:product.field_product_uom_factor /// sería 0.10
	#. **/// f:product.field_product_uom_factor_inv ///**
		Este campo no es editable y se calcula haciendo la inversa del campo anterior ( /// f:product.field_product_uom_factor_inv /// )
	#. **/// f:product.field_product_uom_rounding ///**	
		Este campo se utiliza para hacer un redondeo del valor. Es decir que el vaolor de la unidad que estamos definiendo simpre será múltiplo de /// f:product.field_product_uom_rounding ///
	#. **/// f:product.field_product_uom_active ///**
		Nos puede interesar desactivar esta unidad de medida, de esta forma, no nos aparecerá en la lista de unidades de medida disponibles. Simplemente tendríamos que desactivar est campo. Para volver a habilitar la unidad de medida, volvemos a activar este campo.

	.. note:: Simpre después de cada cambio, clicar en "guardar".


Cálculos de precios
-------------------

En este apartado tenemos dos funcionalidades:

..	_`tipos de precios`:

A) Tipos de precios

	Aquí podemos definir diferentes tipos de precios (coste, venta, neto,...)

	Para crear un nuevo tipo de precio basta con clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

	/// v :product.product_price_type_view ///

	En esta ventana disponemos de los campos /// f:product.field_product_price_type_name ///, /// f:product.field_product_price_type_active ///, /// f:product.field_product_price_type_field /// y /// f:product.field_product_price_type_currency_id ///

	I. **/// f:product.field_product_price_type_name ///**
		Este campo indica el nombre que tendrá este precio.
	#. **/// f:product.field_product_price_type_active ///**
		Este campo indica si este precio está vigente o no (activado o desactivado)
	#. **/// f:product.field_product_price_type_field ///**
		Este campo indica la asociación con los datos de producto. (Precio de coste, precio de venta, precio de venta de distribuidor, ...)
	#. **/// f:product.field_product_price_type_currency_id ///**
		Este campo indica la moneda que utiliza esta tarifa

..	_`Edición de tipos de tarifa`:

#) Tipos de tarifas

	I. **/// f:product.field_product_pricelist_type_name ///**
		Este campo indica el nombre que tendrá la tarifa.
	#. **/// f:product.pricelist.type ///**
		Este campo indica la referencia interna de la tarifa.

Productos por categoría
=======================
	
Este apartado sirve para mostrarnos las categorías de producto en forma de árbol. De esta forma podremos seleccionar los productos que queramos dentro de una categoria determinada

Si clicamos encima, se nos abre otra pestaña con el listado de categorias en forma de árbol. De forma que si clicamos en una categoría en concreto nos abrirá una pestaña con un listado de los productos de esta categoría. (Ver apartado `lista de productos`_)


Tarifas
=======

En este apartado es donde creamos nuestras tarifas. Que podrán tener vigencia en un intervalo de tiempo determinado y se podrán definir en función de los productos o categorías.

Tarifas
-------

Aquí podremos definir o listar las tarifas en función de cuatro campos ( /// f:product.field_product_pricelist_name ///, /// f:product.field_product_pricelist_type ///, /// f:product.field_product_pricelist_currency_id /// y /// f:product.field_product_pricelist_active /// )

Para crear una tarifa nueva, clicamos en el icono de "Nuevo" y nos aparece la siguiente ventana: 
/// v:product.product_pricelist_view ///

**/// f:product.field_product_pricelist_name ///**
	Este campo obligatorio nos indica el nombre de la tarifa que le queremos dar, como podemos ver este campo es traducible.

**/// f:product.field_product_pricelist_type ///**
	Este campo (también obligatorio) nos indica el tipo de tarifa que se utiliza. La definición de los tipos de tarifa, lo vimos en el apartado anterior `Edición de tipos de tarifa`_ 

**/// f:product.field_product_pricelist_currency_id ///**
	Este campo indica el tipo de moneda utilizado por la tarifa que estamos definiendo.

**/// f:product.field_product_pricelist_active ///**
	Al igual que en ocasiones anteriores, este campo sirve para habilitar o deshabilitar la tarifa. Si desmarcamos este campo, por defecto no veremos la tarifa en el listado de tarifas ( a no ser que especifiquemos que queremos ver la lista de tarifas desactivadas.

Desde esta ventana podemos añadir, editar o eliminar una versión de tarifar, aunque también lo podemos hacer desde el menú principal del módulo `Versiones de tarifa`_

Versiones de tarifa
-------------------

Aquí se definen las distintas versiones de tarifa de precios que queramos. Al crear una nueva versión de tarifa, nos aparece la siguiente ventana:
/// v:product.product_pricelist_version_form_view ///

.. _`ver nota`:

.. Note:: Una versión de tarifa está asociada a una Tarifa, por lo tanto si estamos creando una versión de tarifa desde la creación/modificación de una tarifa, no nos aparecerá la opción de escojer la tarifa a la que pertenece (campo /// f:product.pricelist.version.pricelist_id /// ), ya que la asignará automáticamente.

**/// f:product.field_product_pricelist_version_name ///**
	Es indispensable indicar un nombre a la versión de tarifa (también es traducible)

**/// f:product.pricelist.version.pricelist_id ///**
	Indica a la tarifa a la que pertenece (`ver nota`_)

**/// f:product.field_product_pricelist_version_active ///**
	Para habilitar o deshabilitar esta versión de tarifa

**/// f:product.field_product_pricelist_version_date_start ///**
	Fecha que indica el inicio de vigencia de esta versión de tarifa. (Una versión de tarifa tiene una vigencia desde la /// f:product.field_product_pricelist_version_date_start /// hasta la /// f:product.field_product_pricelist_version_date_end ///

**/// f:product.field_product_pricelist_version_date_end ///**
	Fecha que indica el fin de vigencia de esta versión de tarifa.
	
Las versiones de tarifa, tienen una lista de elementos (/// f:product.field_product_pricelist_version_items_id ///). Estos elementos definen por un lado la regla que determina los productos englobados en este elmento y por otro lado definen el precio que se les asocia. Por lo tanto la lista de elementos de la versión de tarifa debe englobar a todos los Productos. Ver `nota sobre elementos`_

.. _`nota sobre elementos`:

.. Note:: como mínimo debe tener un elemento que englobe a todos los productos. 

Al entrar en una nueva línea de elemento de una versión de tarifa se abre la siguiente ventana:

/// v:product.product_pricelist_item_form_view ///

Aquí podemos ver diferenciadas las dos partes que hemos explicado anteriormente (Reglas test de Concordancia y Cálculo de precio). En la primera parte se definen los productos que se quiere tener en cuenta (junto con la cantidad mínima para que así sea) para aplicarles el precio calculado (segunda parte).

Vamos a describir el significado de cada campo:

	**/// f:product.field_product_pricelist_item_name ///**
		Este campo define el nombre de referencia que le pondremos a esta regla (elemento de versión de tarifa). Es aconsejable poner un nombre descriptivo de forma que sepamos a que productos se tendrá en cuenta.
	**/// f:product.field_product_pricelist_item_product_id ///**
		Aquí definimos un producto en concreto. Si no indicamos nada (dejamos vacío el campo), significará que la regla se aplicará para todos los productos de la categoría y/o para todos los productos de una plantilla de producto (ver más abajo).
	**/// f:product.field_product_pricelist_item_product_tmpl_id ///**
		Podemos definir una /// f:product.field_product_pricelist_item_product_tmpl_id /// para definir un conjunto de productos que cumplan unas características determinadas. Describiremos como hacer esta definición al `final de la sección de tarifas`_.		
	**/// f:product.field_product_pricelist_item_categ_id ///**
		Podemos especificar un categoría o subcategoría de productos. Si dejamos este campo vacío, significará que se abarcan todaas las categorías.
	**/// f:product.field_product_pricelist_item_min_quantity ///**
		Esta cantidad significa que se aplicará esta regla sólo cuando se realice un pedido de este producto con esta cantidad o superior. Por ejemplo, si la /// f:product.field_product_pricelist_item_min_quantity /// es 3, y hemos hecho un pedido de este producto pero sólo de 2 unidades, no se aplicará esta regla.
	**/// f:product.field_product_pricelist_item_sequence ///**
		Este número significa el orden de aplicación de las reglas que estamos definiendo. Primero se aplicará la de menor valor. 

	Ahora vamos a ver los campos referentes al cálculo de precio:

	**/// f:product.field_product_pricelist_item_base ///**
		Este valor se toma como referencia para realizar el cálculo de precio. Las opciones que nos aparecen para escojer son `tipos de precios`_, otra tarifa (que hayamos definido previamente) o la opción `"Sección empresa del formulario de producto"`_.
	**/// f:product.field_product_pricelist_item_base_pricelist_id ///**
		Este campo sólo estará habilitado si hemos escogido la opción "otra tarifa" y nos permite escoger una de las tarifas que tengamos definidas.
	**/// f:product.field_product_pricelist_item_price_discount ///**
		Este campo se utiliza para establecer un descuento o un incremento en el precio base expresado en centésimas de unidad. Es decir, para incrementar el precio en un 24% , debemos llenar este campo con 0.24, si quisiéramos aplicar un descuento del 10% pondríamos -0.10.
	**/// f:product.field_product_pricelist_item_price_surcharge ///**
		Este campo nos permite añadir un valor fijo (después de descuento / incrementos)
	**/// f:product.field_product_pricelist_item_price_round ///**
		Este valor se utiliza para redondear el precio final. Los valores resultantes siempre serán múltiplos de este valor.
	**/// f:product.field_product_pricelist_item_price_min_margin ///**
		Este valor se utiliza como limitador inferior del precio calculado. Es decir, que si el precio calculado es inferior a este valor, el precio final será el valor del /// f:product.field_product_pricelist_item_price_min_margin ///
	**/// f:product.field_product_pricelist_item_price_max_margin ///**
		Este valor se utiliza como limitador superior del precio calculado. Es decir, que si el precio calculado es superio a este valor, el precio final será el valor del /// f:product.field_product_pricelist_item_price_min_margin ///


**Resumen del cálculo del precio**
	::

        	1. Se aplica el descuento al precio base (tanto sea negativo = descuento, como positivo = subida de precio)
        
        	2. Se redondea (precisión)
        
        	3. Se le incrementa el valor fijo (ver nota) 
        
        	4. a. Si el resultado es menor que el Margen mínimo, el valor final será el Margen mínimo.
        
        	   b. Si el resultado es mayor que el Margen máximo, el valor final será el Margen máximo.
        
        	   c. Si el resultado está entre el Margen mínimo y el máximo, el valor final será ese mismo resultado.


..	Note:: 	Es recomendable que el valor fijo cumpla los requisitos de la precisión que buscamos. Ejemplo: si la precisión es 0.10, el valor fijo no debería ser 1.25, debería ser 1.20 o 1.30. También es recomendable que el /// f:product.field_product_pricelist_item_price_min_margin /// y el /// f:product.field_product_pricelist_item_price_max_margin /// cumplan los requisitos de precisión.



..	_`final de la sección de tarifas`:

..	_`lista de productos`:

Productos
=========

En este apartado vamos a ver como se define un producto. Cuando abrimos la ventana de nuevo producto
/// v:product.product_normal_form_view ///
podremos ver existen 2 zonas diferenciadas. La primera zona (superior) tenemos una serie de campos. En la segunda (inferior) aparecen una serie de pestañas, cada una de las cuales contiene sus campos específicos.

Primero describimos los campos de la primera zona (comunes) y luego iremos describiendo cada una de las pestañas.

	**/// f:product.field_product_template_name ///**
		En este campo guardamos el nombre del producto. Recordar que los campos en azul són obligatorios
	**/// f:product.field_product_product_variants ///**
		Puede darse el caso de que para un mismo producto, queramos utilizar variantes. Por ejemplo, podríamos diferenciar un mismo producto por colores o por estampados.
	**/// f:product.field_product_product_code ///**
		Este campo se puede utilizar para referenciar el producto. Es un código interno que nos puede facilitar la búsqueda.
	**/// f:product.field_product_product_ean13 ///**
		Aquí es donde podemos guardar el código EAN13 (código de barras) del producto.
        **/// f:product.field_product_template_sale_ok ///**	
		En este campo indicamos si el producto es vendible (activado) o no (desactivado). Tener en cuenta que un producto puede ser comprable,vendible y alquilable a la vez (los campos no son exclusivos)
        **/// f:product.field_product_template_purchase_ok ///**	
		En este campo indicamos si el producto es comprable (activado) o no (desactivado). Tener en cuenta que un producto puede ser comprable, vendible y alquilable a la vez (los campos no son exclusivos)
        **/// f:product.field_product_template_rental ///**	
		En este campo indicamos si el producto es alquilable (activado) o no (desactivado). Tener en cuenta que un producto puede ser comprable, vendible y alquilable a la vez (los campos no son exclusivos)


	Ahora describiremos los campos de cada una de las pestañas

Información
-----------

        **/// f:product.field_product_template_type ///**	
		Existen 3 tipos: *Almacenable*, *Consumible* y *Servicio*

		:Almacenable: Se tiene en cuenta el estoc, por ejemplo para posibles pedidos a proveedor.
		:Consumible: Se asume que tiene stock infinito. Se suele utilizar para tener en cuenta un producto de uso interno que no interviene en las ventas a clientes.
		:Servicio: Se utiliza cuando no es un producto físico. Por ejemplo, sería si quisiéramos tener un control de las horas utilizadas como servicio, y el producto podría ser soporte, análisis, estudio, etc...

        **/// f:product.field_product_template_procure_method ///**	
		Existen dos tipos: *obtener por estoc* y *obtener bajo pedido*

		:Por estoc: Se tiene en cuenta la cantidad de prodructo (estoc) para realizar diferentes tareas, como por ejemplo pedidos. Esta opción es muy útil cuando se tienen otros módulos instalados ( como por ejemplo el módulo de stocks )
		:Bajo pedido: Se tiene en cuenta en el momento que se realiza un pedido para realizar diferentes tareas, como por ejemplo pedidos a proveedor. Esta opción es muy útil cuando se tienen otros módulos instalados ( como por ejemplo el módulo de stocks )
        **/// f:product.field_product_template_supply_method ///**	
		Existen dos tipos: *Producir* y *Comprar*

		:Producir: Significa que para que dispongamos de este producto, previamente se debe producir.
		:Comprar: Significa que para obtener este producto, tiene que haber una compra a proveedor.

        **/// f:product.field_product_template_categ_id ///**	
		Aquí podremos seleccionar una de las `Categorías de productos`_ que hayamos definido anteriormente para asociarla a esa categoría.
        **/// f:product.field_product_template_state ///**	
		Podremos escojer entre 4 opciones predefinidas o dejar este campo en blanco (ya que no es obligatorio).

		:En desarrollo: Normalmente se le asigna este valor cuando todavía no está operativo.
		:En producción: Se le puede asignar cuando está en período de producción o cuando ya está operativo.
		:Fin del ciclo de vida: Puede indicar que este producto ya no está vendible porque finalizó su ciclo de vida.
		:Obsoleto: Se suele marcar para indicar que ya no se utilizará más, pero no lo eliminamos para poder hacer consultas sobre él.

		Estos valores pueden ser útiles para poder filtrar los productos que cumplen un tipo estado.

        **/// f:product.field_product_template_product_manager ///**	
		Como su propio nombre indica, se puede utilizar si queremos asignar una persona como /// f:product.field_product_template_product_manager ///.
..	_`unidad de medida de venta`:

        **/// f:product.field_product_template_uos_id ///**	
		En este campo podremos seleccionar una `unidad de medida`_ de las que hayamos definido anteriormente.
        **/// f:product.field_product_template_uos_coeff ///**	
		Este campo relaciona la `unidad de medida`_ del anterior campo con la `unidad de medida de venta`_. Por ejemplo, podríamos tener un producto que fabricamos y almacenamos en unidades pero que las vendiéramos en cajas de 10 unidades.
        **/// f:product.field_product_template_mes_type ///**	
		Podemos escojer entre *Fijo* y *Variable*
        **/// f:product.field_product_template_volume ///**	
		Valor de /// f:product.field_product_template_volume /// del producto expresado en m³
        **/// f:product.field_product_template_weight ///**	
		Valor de /// f:product.field_product_template_weight /// del producto expresado en Kg
        **/// f:product.field_product_template_weight_net ///**	
		Valor de /// f:product.field_product_template_weight /// del producto expresado en Kg
        **/// f:product.field_product_template_uom_id ///**	
		Unidad de medida por defecto utilizada para todas las operaciones de stock.
        **/// f:product.field_product_template_uom_po_id ///**	
		Unidad de medida utilizada en las órdenes de compra.

Abastecimiento y Ubicaciones
----------------------------

        **/// f:product.field_product_template_sale_delay ///**	
		Es el tiempo que se le notifica al cliente que tardará su pedido en llegarle desde que se confirma el pedido.
        **/// f:product.field_product_template_produce_delay ///**	
		Es el tiempo que se estima necesario para producir este producto.
        **/// f:product.field_product_template_warranty ///**	
		Es el número de meses que cubre la garantía del producto.
        **/// f:product.field_product_product_active ///**	
		Este campo indica si el producto está activo o no. Hay que tener en cuenta que si desactivamos este campo, al hacer un listado de productos, no nos aparecenran los productos que no estén activos (a no ser que especifiquemos que nos muestre solo los que no estén activos).
        **/// f:product.field_product_template_company_id ///**	
		Este es un campo que determina la compañía a la que pertenece el producto.
        **/// f:product.field_product_template_loc_rack ///**	
		Es la referencia que utilizamos para ubicar este producto en nuestro almacén. Concretamente, la estantería donde estará ubicado.
        **/// f:product.field_product_template_loc_row ///**	
		Es la referencia que utilizamos para ubicar este producto en nuestro almacén. Concretamente, la fila donde estará ubicado.
        **/// f:product.field_product_template_loc_case ///**	
		Es la referencia que utilizamos para ubicar este producto en nuestro almacén. Concretamente, la caja donde estará ubicado.

..	_`"Sección empresa del formulario de producto"`:

Precios y proveedores
---------------------

Precios base:
        **/// f:product.field_product_template_standard_price ///**	
		Este campo nos determina el precio de coste del producto. Este campo se tendrá en cuenta para calcular el precio de venta, según la tarifa que se aplique.
        **/// f:product.field_product_product_price_margin ///**	
		Campo de tipo porcentaje, que se utiliza para calcular el precio de un producto de tipo variante. Ver `cálculo lista de precios`_.
        **/// f:product.field_product_template_cost_method ///**	
		Campo que indica el método que utilizará OpenERP para calcular el valor de coste del estoc. Cuando se realiza una recepción de productos, se guarda el precio de coste. Si hemos seleccionado "Precio estándar", cuando hagamos un cálculo del valor del estoc, tomará como referencia el precio de coste actual de cada producto. En cambio si hemos seleccionado el "Precio promedio", el cálculo del valor del estoc tendrá en cuenta los diferentes precios de coste de los productos recepcionados y hará una media.
        **/// f:product.field_product_template_list_price ///**	
		Campo que se utiliza para calcular el precio de lista (precio al público).
        **/// f:product.field_product_product_price_extra ///**	
		Campo expresado en Euros o en la moneda que se corresponda, que se utiliza para calcular el precio de un producto de tipo variante. Ver `cálculo lista de precios`_.
..	_`cálculo lista de precios`:

	Precio de Lista (precio de venta al público) = (/// f:product.field_product_template_standard_price /// * /// f:product.field_product_product_price_margin ///) + /// f:product.field_product_product_price_extra ///

Proveedores:
	Aquí es donde podemos añadir los diferentes provevedores del producto. Para añadir un proveedor, tenemos que clicar en el icono de "Nuevo" que hay debajo del campo /// f:product.field_product_product_price_extra ///. Se nos habrirá la siguiente ventana:

	/// v: product.product_supplierinfo_form_view ///
 
	Vamos a describir cada uno de los campos que hay en el formulario de proveedores:

        **/// f: product.field_product_supplierinfo_name ///**	
		Nombre de la empresa proveedora.
        **/// f:product.field_product_supplierinfo_product_name ///**	
		Denominación del producto por parte del proveedor.
        **/// f:product.field_product_supplierinfo_delay ///**	
		Tiempo estimado (en días) que tardará el proveedor para servirnos el producto. Se cuenta el tiempo desde que se confirma el pedido hasta que el producto llega a nuestra empresa.
        **/// f:product.field_product_supplierinfo_sequence ///**	
		Este campo establece el orden de preferencia a tener en cuenta cuando se realice un pedido. Es decir, si definimos varios proveedores, será el orden de prioridad para escojer de forma automática el proveedor.
        **/// f:product.field_product_supplierinfo_product_code ///**	
		Código de referencia que utiliza el proveedor para el producto.
        **/// f:product.field_product_supplierinfo_qty ///**	
		/// f:product.field_product_supplierinfo_qty /// de producto que requiere el proveedor para poder realizarle un pedido.
	En esta ventana, podemos definir diferentes precios (de proveedor) en función de la cantidad pedida. Para realizar esto, debemos clicar en el icono de "Nuevo" y nos situará en la columna de /// f:product.field_pricelist_partnerinfo_min_quantity /// en el recuadro inferior. Aquí podremos escribir directamente la cantidad. Seguidamente estableceremos el precio clicando encima del campo /// f:product.field_pricelist_partnerinfo_price /// de la línea que estamos editando.
	Podemos añadir tantas líneas como precios dispongamos (en función de las cantidades).

Descripciones
-------------
	En esta pestaña tenemos tres campos de descripción del producto. A demás, estos campos son traducibles.

        **/// f:product.field_product_template_description ///**	
		Descripción interna que utilizaremos nosotros.
        **/// f:product.field_product_template_description_sale ///**	
		Descripción de venta que se utilizará cuando enviémos documentación al proveedor ( por ejemplo un pedido de compra ).
        **/// f:product.field_product_template_description_purchase ///** 
                Descripción de compta que se utilizará cuando enviémos documentación a nuestro cliente (por ejemplo un albarán de entrega o una factura)	

Empaquetado
-----------

En esta pestaña podemos introducir datos referentes al empaquetado del producto. Para introducir los datos, tenemos que clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

/// v: product.product_packaging_form_view ///

**/// f:product.field_product_packaging_ean ///**	
        Código EAN  (código de barras) del empaquetado del producto. Puede ser diferente del EAN del producto.

**/// f:product.field_product_packaging_qty ///**	
        Cantidad de unidades que van en un paquete.

**/// f:product.field_product_packaging_weight_ul ///**	
        Peso del paquete en vacío.

**/// f:product.field_product_packaging_sequence ///**	
        Número de secuencia del paquete. Podría ser que un producto llegue en varios paquetes, este campo establece cual es de estos paquetes.

**/// f:product.field_product_packaging_ul ///**	
        Campo que define el tipo de empaquetado. Podemos seleccionar uno existente o definir varios. Si definimos uno nuevo, estableceremos una descripción del paquete y uno de los siguientes tipos (Unidad, Paquete, Caja o Palet).

Paletización:

**/// f:product.field_product_packaging_ul_qty ///**	
        Campo que determina, cuantas unidades de producto caben en un piso de un palet o paquete.

**/// f:product.field_product_packaging_weight ///**	
        El peso total de un palet o paquete lleno de este producto.

**/// f:product.field_product_packaging_rows ///**	
        Número de pisos de paquetes que caben en un palet o paquete.

Dimensiones del Palet:

**/// f:product.field_product_packaging_height ///**	
        /// f:product.field_product_packaging_height /// total de un palet o paquete lleno de este producto.

**/// f:product.field_product_packaging_length ///**	
        /// f:product.field_product_packaging_length /// del palet o paquete lleno de este producto.	

**/// f:product.field_product_packaging_width ///**	
        /// f:product.field_product_packaging_width /// del palet o paquete lleno de este producto.	

**/// f:product.field_product_packaging_name ///**	
        /// f:product.field_product_packaging_name /// del paquete




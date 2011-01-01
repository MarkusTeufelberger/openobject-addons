.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

-------------------
Gestión de Empresas
-------------------

Empresas
========

/// m: base.menu_partner_form ///

Vamos a ver los campos de la ficha de creación de una empresa.

/// v: base.view_partner_form ///


*Campos genéricos de empresas*

/// f: base.field_res_partner_name ///:
   Especifica el nombre de la empresa.
     
/// f: res.partner.ref ///:
   Especifica el código de referencia de la empresa.

/// f: res.partner.customer ///:
   Indica si la empresa es de tipo Cliente o no. 

   ..              note::      Una empresa puede ser cliente y proveedora a la vez.

/// f: res.partner.title ///:
   Indica el tipo de empresa o como nos dirigimos a ella.

/// f: res.partner.lang ///:
   Idioma por defecto que utiliza. Esto nos puede ser útil para generar documentación al cliente (facturas, etc..)

/// f: res.partner.supplier ///:
   Indica si la empresa es proveedora nuestra o no.

	
Como podemos ver, la ficha tiene varias pestañas. Iremos viendo los campos de cada una de las pestañas.

General
-------

Los campos que podemos encontrarnos en esta pestaña son los siguientes

/// f: res.partner.address.name ///:
   Nombre del contacto de la empresa.

/// f: res.partner.address.title ///:
   Distinción o forma de dirigirse a la persona de contacto.

/// f: res.partner.address.function ///:
   Función que desempeña la persona de contacto.

/// f: res.partner.address.type ///:
   Tipo de dirección, es decir, funcionalidad de la misma (para que la utilizaremos).

/// f: base.field_res_partner_address_street ///:
   Nombre de la calle.

/// f: res.partner.address.street2 ///:
   Ampliación del nombre de calle (por si no fuera suficiente con el campo anterior).

/// f: res.partner.address.zip ///:
   Código postal de la dirección.

/// f: res.partner.address.city ///:
   Ciudad a la que pertenece.

/// f: res.partner.address.country_id ///:
   País.

/// f: res.partner.address.state_id ///:
   Provincia.

/// f: res.partner.address.phone ///:
   Teléfono fijo.

/// f: res.partner.address.fax ///:
   Número de Fax.

/// f: res.partner.address.mobile ///:
   Número de teléfono móvil.

/// f: res.partner.address.email ///:
   Dirección de correo electrónico.

*Categorias*

/// f: res.partner.category.name ///:
   Nombre de la categoría de la empresa.

/// f: res.partner.category.active ///:
   Indica si esta categoría está activa o está deshabilitada.

/// f: res.partner.category.parent_id ///:
   Categoría padre a la que pertenece.

Ventas & Compras
----------------

Los campos que podemos encontrarnos en esta pestaña son los siguientes

/// v: base.view_partner_form : website ///

/// f: res.partner.user_id ///:
   Usuario interno que se encarga de comunicarso con est empresa.

/// f: res.partner.active ///:
   Indica si la empresa está activa o deshabilitada.

/// f: res.partner.website ///:
   Dirección de la página web.

/// f: res.partner.date ///:
   Fecha en la que se dá de alta la empresa.

/// f: res.partner.parent_id ///:
   Empresa a la que pertenece.

Historial
---------

Los campos que podemos encontrarnos en esta pestaña son los siguientes

/// v: base.view_partner_form : events ///

/// f: res.partner.events ///:
   Al crear un nuevo evento nos aparece la siguiente ficha

   /// v: base.res_partner_event-wopartner-view_form ///

   /// f: res.partner.event.name ///:
      Nombre descriptivo del evento que estamos definiendo.

   /// f: res.partner.event.partner_type ///:
      Normalmente un de estas tres (Cliente, Proveedor o Prospección comercial) 

   /// f: res.partner.event.som ///:
      Como su propio nombre indica, es el grado de satisfacción con la empresa.

   /// f: res.partner.event.date ///:
      Fecha del evento.

   /// f: res.partner.event.canal_id ///:
      Tipo de medio utilizado con la empresa.

   /// f: res.partner.event.type ///:
      Normalmente 3 posibles valores ( Oportunidad de venta, Oferta de compra o Contacto de prospección )

   /// f: res.partner.event.user_id ///:
      Usuario que podrá gestionar este evento.

   /// f: res.partner.event.probability ///:
      Porcentaje de probabilidad (1.0 = 100%, 0.2 = 20%)

   /// f: res.partner.event.planned_revenue ///:
      Dinero previsto que nos devuelvan con la acción (evento) actual.

   /// f: res.partner.event.planned_cost ///:
      Cantidad de dinero que se prevee que tengamos que enviar.

   /// f: res.partner.event.description ///:
      Descripción libre de lo que realiza el evento.

   /// f: res.partner.event.document ///:
      Por si quisiéramos adjuntar un archivo o documento relacionado.

Notas
-----

Los campos que podemos encontrarnos en esta pestaña son los siguientes

/// v: base.view_partner_form : comment ///

/// f: res.partner.comment ///:
   Aquí podemos escribir las notas que queramos.


..   _`Fin Empresas básico`:


--------------------------
Administración del sistema
--------------------------

Esta sección va dirigida a administradores y usuarios avanzados.

El fichero de configuración
===========================

Es posible establecer algunos parámetros de configuración del servidor de OpenERP (openerp-server.py) mediante un fichero de configuración. Los parámetros aceptados en este fichero son los siguientes:

port
  Establece el puerto que se utilizará para escuchar las peticiones XML-RPC.

netport
  Establece el puerto que se utilizará para escuchar las peticiones Net-RPC.


Menú Configuración
==================

Secuencias
----------

En /// m: base.menu_ir_sequence_form /// podremos gestionar las secuencias, que permiten determinar como van a generarse los nuevos números de albarán, factura o cualquier otro documento del sistema.

/// v : base.sequence_view ///

Tipos de secuencias
-------------------

En /// m: base.menu_ir_sequence_type_form_form/// podremos gestionar los tipos de secuencias.

/// v: base.sequence_type_form_view /// 


Usuarios
========

Usuarios
--------

	Apartado donde podemos añadir, modificar y eliminar un usuario.

	Al acceder a esta opción se nos abre una pestaña en vista de tipo lista donde podremos ver los usuarios creados hasta este momento.

- Añadir nuevo usuario

	después nos aparecerá la ficha del nuevo usuario. Hay que tener en cuenta que los campos que están en azul son necesarios.

	A destacar dos campos:
  
	Campo *'Acción Inicial'* : Aquí podemos assignar un menú para que aparezca una nueva pestaña en el menu inicial cuando el usuario entre en la aplicación.

	*Firma* : Este campo puede ser interesante si se quiere tener una firma determinada, que se tendrá en cuanta al enviar e-mails.


- Modificar usuario
	Para acceder a esta opción, solo es necesario hacer doble clic encima del usuario correspondiente.

- Eliminar usuario
	Para eliminar un usuario, hemos de clickar en el icono "eliminar". Hay que tener en cuenta que se nos preguntará si estamos seguros.

Grupos
------

Seguridad
=========




On Demand Control
=================

1. Hours per User

Sección donde podemos ver de forma gráfica, el número de hora que se ha utilizado OpenERP por usuario.
Podemos escojer el rango entre fechas que queramos, y nos mostrará un gráfico.


	.. |DIA| date:: %d
	.. |MES| date:: %m
	.. |AÑO| date:: 20%y



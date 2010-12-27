.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

-----------------------
Contabilidad y finanzas
-----------------------

Descripción
===========

Este módulo, nos habilita OpenERP para gestionar la Contabilidad de la empresa (Contabilidad general, Costes / contabilidad analítica, Contabilidad de terceros, Gestión de impuestos, Presupuestos, Facturas de clientes y proveedores, Extractos de cuentas bancarias, ... ). A continuación describiremos más en detalle cada una de las funcionalidades.

Podremos ver que nos ha aparecido una nueva funcionalidad en el menú principal. En este caso 'Contabilidad y finanzas'. También podremos ver que nos aparecerán nuevas funcionalidades en los módulos instalados anteriormente.


Configuración
=============

Contabilidad financiera
-----------------------

**Periodos**
	En este apartado se definen dos conceptos. Ejercicio fiscal y periodo:

	*Ejercicio fiscal*
		Al crear un nuevo ejercicio fiscal (clicando el icono "Nuevo") nos aparece la siguiente ventana.

		/// v: account.view_account_fiscalyear_form ///

                /// v: account.fiscalyear_form ///

		En esta ventana podemos ver los siguientes campos:

		**/// f:account.fiscalyear.name ///**
			En este campo introduciremos el nombre que le queremos dar al /// f:account.fiscalyear.name ///.
		**/// f:account.fiscalyear.code ///**
			Este campo denota el código interno que utilizaremos para hacer referencia al Ejercicio fiscal
		**/// f:account.fiscalyear.date_start ///**
			Este campo determina el inicio del Ejercicio fiscal.
		**/// f:account.fiscalyear.date_stop ///**
			Este campo determina la fecha final del Ejercicio fiscal.
		**/// f:account.fiscalyear.end_journal_period_id ///**
			En este campo indicaremos el diario de asientos a utilizar. 
		**/// f:account.fiscalyear.state ///**
			Este campo, que lo podemos encontrar en la parte inferior de la ventana, nos indica el estado en el que se encuentra el ejercicio.

		En esta ventana también podemos definir `los periodos`_ de que consta el ejercicio.

..	_`los periodos`:

	*Periodo*
		Como podemos ver, se pueden definir de forma automática periodos mensuales o trimestrales, clicando en el correspondiente botón ("Crear periodos mensuales" o "Crear periodos trimestrales") en la parte inferior.
		De todas formas podemos crearlos de forma manual clicando en el icono de "Nuevo" y nos aparecerá la siguiente ventana:
	
		/// v:account.view_account_period_form ///

		Esta ventana tiene los siguientes campos:

		**/// f:account.period.name ///**
			Nombre que le queremos dar a este periodo.
		**/// f:account.period.code ///**
			Código que le asignamos a este periodo.
		**/// f:account.period.date_start ///**
			Fecha de inicio del periodo.
		**/// f:account.period.date_stop ///**
			Fecha final del periodo.
		**/// f:account.period.special ///**
			Indica si este es un periodo de apertura o de cierre. Si está marcado este campo, implica que este periodo se puede solapar con otro periodo. Por ejemplo, si estamos definiendo el periodo de apertura del presente año, se podrá solapar con el periodo del primer trimestre o primer mes.
	
**Cuentas generales**
	
	*Listado de cuentas*

		Desde este apartado podemos ver el llistado de cuentas o ( clicando en "Nuevo" ) podemos añadir una nueva cuenta.
	
		Al crear una nueva cuenta nos aparece la siguiente ventana:

		/// v:account.view_account_form ///

		Detalle de los campos:

		/// f:account.account.name ///

			Nombre de la cuenta.

		/// f:account.account.code ///

			Código de la cuenta.

		/// f:account.account.parent_id ///

			Esta es la cuenta a la que pertenece la cuenta que estamos modificabdo.

		/// f:account.account.company_id ///

			Este campo indica la compañía a la que estamos asignando una cuenta, es decir nuestra compañía.

		/// f:account.account.user_type ///

			Este campo nos permite seleccionar alguno de los `tipos de cuenta`_ creados.

		Podemos observar que tenemos 2 pestañas. La primera pestaña "Información general" y "Notas". En la pestaña de Información general tenemos los siguientes campos:

		/// f:account.account.currency_id ///
			
			Indica la moneda que utilizará esta cuenta.

		/// f:account.account.currency_mode ///

			Existen dos posibles valores. "En fecha" o "Tasa Promedio". Lo que está indicando este campo es como realizar la conversión de moneda. Si se indica "En fecha", tomaremos como referencia de cambio de moneda la que exista en la fecha actual.

		/// f:account.account.reconcile ///

			El campo (activo o desactivado) indica si queremos que esta cuenta sea conciliable o no.

		/// f:account.account.active ///

			Como su nombre indica, si este campo está activo indica que la cuenta está activa.

		/// f:account.account.check_history ///

			Este campo indica si se imprimen todos los asientos al imprimir el libro mayor (campo activado) o por el contrario, solo se imprimirá el balance de esta cuenta (campo desactivado).

		/// f:account.account.type ///

			Este campo nos define el tipo de cuenta para la que la utilizaremos. Los posibles valores son "A Cobrar", "A Pagar" , "Vista", "Consolidaciones", "Otros" o "Cierre". A continuación enumeramos cada posible valor y su significado.

			"A Cobrar"

				

		/// f:account.account.tax_ids ///

		/// f:account.account.child_consol_ids ///

		/// f:account.account.note ///
	
	*Plan contable*

..	_`tipos de cuenta`:

	*Tipos de cuenta*

**Diarios financieros**

**Impuestos**

**Plantillas**

**Posiciones fiscales**

Contabilidad analítica
-----------------------

**Cuentas analíticas**

**Definición de diario analítico**

Definición de modelos de asientos
---------------------------------

Plazos de pago
--------------

	En este apartado

Monedas
-------

Codificación de asientos
========================




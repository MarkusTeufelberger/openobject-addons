.. Copyright (C) 2010 - NaN Projectes de Programari Lliure, S.L.
..                      http://www.NaN-tic.com
.. Esta documentación está sujeta a una licencia Creative Commons Attribution-ShareAlike 
.. http://creativecommons.org/licenses/by-sa/3.0/

||| : before : base.historial |||
/// f: res.partner.property_product_pricelist ///:
   Tarifa a utilizar por esta empresa (sustituye a la tarifa por omisión).

||| : before : base.historial |||
*Propiedades de Venta*

||| : after : base.fin_empresas_basico |||

Contabilidad
------------

*Propiedades de contabilidad del cliente*
		
/// f:account.field_res_partner_property_account_receivable ///:
  Este campo obligatorio nos indica a qué cuenta financiera se computará el cobro. Podemos seleccionar una genérica o crear una específica para esta empresa.

/// f:account.field_res_partner_property_account_payable ///:
  Este campo obligatorio nos indica a qué cuenta financiera se computará el pago. Podemos seleccionar una genérica o crear una específica para esta empresa.

/// f:account.field_res_partner_property_account_position ///:
  Este campo determina la posición fiscal para poder determinar los impuestos que se le aplicarán.

/// f:account.field_res_partner_property_payment_term ///:
  Este campo indica el plazo de pago. podemos escoger entre la lista de plazos de pago que hayamos definido en /// m: account.menu_action_payment_term_form ///.

/// f:account.field_res_partner_credit ///:
  Este campo nos indica la cantidad en Euros que nos debe esta empresa (Facturas pendientes de pagar,etc...)

/// f:base.field_res_partner_credit_limit ///:
  Aquí podemos indicar la cantidad que nosotros hemos establecido como límite máximo de crédito para esta empresa.

/// f:account.field_res_partner_debit ///:
  Este campo indica lo que nosotros debemos a esta empresa. Por ejemplo, si esta empresa es un proveedor y tiene una factura pendiente de que la abonemos.
	
Podemos ver que debajo de los campos mencionados, tenemos una lista de números de cuenta (datos relativos a los bancos). En este apartado nos permite añadir/modificar o eliminar cuentas bancarias relacionadas con la empresa que estamos modificando. Para crear una nueva cuenta, basta con clicar en el icono de "Nuevo" y nos aparecerá la siguiente ventana:

/// v: base.view_partner_form : bank_ids ///

*Describiremos los distintos campos*

/// f:base.field_res_partner_bank_state ///:
  Este campo indica el tipo de banco de que se trata. En principio, si no se ha instalado ningún otro módulo. Sólo nos aparecerá el tipo "Cuenta Bancaria".

/// f:base.field_res_partner_bank_acc_number ///:
  Aquí es donde indicaremos el número de cuenta bancaria.

/// f:base.field_res_partner_bank_bank ///:
  En este campo podemos escribir el nombre del banco (para que nos sirva de referencia).

/// f:base.field_res_partner_bank_sequence ///:
  Este campo indica el número de orden (prioridad) en el que nos mostrará la lista de cuentas (si es que tenemos más de una). 

/// f:base.field_res_partner_bank_name ///:
  Aquí podemos escribir lo que queramos. Por ejemplo, podríamos anotar la dirección de la oficina a la que pertenece esta cuenta.

/// f:base.field_res_partner_bank_owner_name ///:
  Aquí indicamos el titular de la cuenta.

/// f:base.field_res_partner_bank_street ///:
  Describe la calle del titular de la cuenta. Normalmente este y los sucesivos campos, denotan la dirección fiscal de la empresa.

/// f:base.field_res_partner_bank_zip ///:
  Código postal

/// f:base.field_res_partner_bank_city ///:
  Ciudad

/// f:base.field_res_partner_bank_country_id ///:
  País

/// f:base.field_res_partner_bank_state_id ///:
  Normalmente indica la provincia.


||| : append : base.v_base_sequence_view |||

En la pestaña "Ejercicios fiscales", podremos determinar el comportamiento de la secuencia según el ejercicio fiscal en el que se encuentre el documento. Los campos a rellenar son /// f:account.field_account_sequence_fiscalyear_fiscalyear_id /// y /// f:account.field_account_sequence_fiscalyear_sequence_id ///

/// v: base.sequence_view : fiscal_ids ///



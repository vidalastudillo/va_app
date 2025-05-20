/* -----------------------------------------------------------------------------
Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-03

--------------------------------------------------------------------------------
Propósitos:
--------------------------------------------------------------------------------

- Establece los valores de los campos que dependen de otros

--------------------------------------------------------------------------------
Implementación:
--------------------------------------------------------------------------------

Este script debe estar guardado en la sección de ERPNext `Client Script` en un
registro con los siguientes datos:

`Name`: `DIAN tercero` (O cualquier otro descriptivo)
`DocType`: `DIAN tercero`
`Apply To': `Form`
`Enabled`: `True`

--------------------------------------------------------------------------------
Requerimientos:
--------------------------------------------------------------------------------

- Ninguno.
		// frm.set_value("div", frm.doc.div =  * frm.doc.basic)

----------------------------------------------------------------------------- */


/**
 * Evalúa eventos que ben desencadenar la llamada a las funciones que hacen
 * cálculos.
 */
frappe.ui.form.on('DIAN tercero', {
    nit: function(frm) {
        perform_changes_on_field_div(frm);
    },
    razon_social: function(frm) {
        perform_changes_on_field_nombre_completo(frm);
    },
    primer_apellido: function(frm) {
        perform_changes_on_field_nombre_completo(frm);
    },
    segundo_apellido: function(frm) {
        perform_changes_on_field_nombre_completo(frm);
    },
    primer_nombre: function(frm) {
        perform_changes_on_field_nombre_completo(frm);
    },
    otros_nombres: function(frm) {
        perform_changes_on_field_nombre_completo(frm);
    },
    refresh: function(frm) {
        perform_changes_on_field_div(frm);
        perform_changes_on_field_nombre_completo(frm);
    }
});

/**
 * Se ocupa de efectuar el cambio en el campo DIV (Dígito de Verificación).
 */
function perform_changes_on_field_div(frm) {
    if (!frm.doc.nit) {
        frm.set_value('div', '');
        return;
    }

    // Call the calculation function from the NIT as a string
    let nitStr = calcularDigitoVerificacion(frm.doc.nit.toString());
    frm.set_value('div', nitStr);
}

/**
 * Se ocupa de efectuar el cambio en el campo Nombre Completo
 * para construirlo a partir del contenido de otros.
 */
function perform_changes_on_field_nombre_completo(frm) {
    
    let nombre_completo = [frm.doc.razon_social, frm.doc.primer_apellido, frm.doc.segundo_apellido, frm.doc.primer_nombre, frm.doc.otros_nombres].filter(Boolean).join(" ");
    frm.set_value('nombre_completo', nombre_completo);
}

// Sigue código tomado de:
// https://github.com/gabrielizalo/calculo-digito-de-verificacion-dian

/**
 * Permite calcular el dígito de verificación.
 * 
 * @param {string} myNit - NIT proporcionado por el RUES a la empresa.
 * @returns {Number} Retorna el número de verificación que corresponde a la empresa.
 */
function  calcularDigitoVerificacion ( myNit )  {
    var vpri,
        x,
        y,
        z;
    
    // Se limpia el Nit
    myNit = myNit.replace ( /\s/g, "" ) ; // Espacios
    myNit = myNit.replace ( /,/g,  "" ) ; // Comas
    myNit = myNit.replace ( /\./g, "" ) ; // Puntos
    myNit = myNit.replace ( /-/g,  "" ) ; // Guiones
    
    // Se valida el nit
    if  ( isNaN ( myNit ) )  {
      console.log ("El nit/cédula '" + myNit + "' no es válido(a).") ;
      return "" ;
    };
    
    // Procedimiento
    vpri = new Array(16) ; 
    z = myNit.length ;
  
    vpri[1]  =  3 ;
    vpri[2]  =  7 ;
    vpri[3]  = 13 ; 
    vpri[4]  = 17 ;
    vpri[5]  = 19 ;
    vpri[6]  = 23 ;
    vpri[7]  = 29 ;
    vpri[8]  = 37 ;
    vpri[9]  = 41 ;
    vpri[10] = 43 ;
    vpri[11] = 47 ;  
    vpri[12] = 53 ;  
    vpri[13] = 59 ; 
    vpri[14] = 67 ; 
    vpri[15] = 71 ;
  
    x = 0 ;
    y = 0 ;
    for  ( var i = 0; i < z; i++ )  { 
      y = ( myNit.substr (i, 1 ) ) ;
      // console.log ( y + "x" + vpri[z-i] + ":" ) ;
  
      x += ( y * vpri [z-i] ) ;
      // console.log ( x ) ;    
    }
  
    y = x % 11 ;
    // console.log ( y ) ;
  
    return ( y > 1 ) ? 11 - y : y ;
}

/* -----------------------------------------------------------------------------

Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-04

--------------------------------------------------------------------------------
Propósitos:
--------------------------------------------------------------------------------

- Extraer la información que contienen los archivos .XML de los documentos
  electrónicos de la DIAN.
- Permitir la generación de documentos ERPNext usando la información extraída.

--------------------------------------------------------------------------------
Implementación:
--------------------------------------------------------------------------------

Este script debe estar guardado en la sección de ERPNext `Client Script` en un
registro con los siguientes datos:

`Name`: `DIAN Document` (O cualquier otro descriptivo)
`DocType`: `DIAN document`
`Apply To': `Form`
`Enabled`: `True`

--------------------------------------------------------------------------------
Requerimientos:
--------------------------------------------------------------------------------

- Ninguno.

----------------------------------------------------------------------------- */

/**
 * Botones para ejecutar procesos sobre los documentos
 */
frappe.ui.form.on("DIAN document", {
  refresh: function(frm) {

    // Update XML button
    frm.add_custom_button("Update DOC from XML", function() {
      if (!frm.doc.xml) {
        frappe.msgprint(__("Please attach an XML first."));
        return;
      }
      frappe.call({
        method: "va_app.va_dian.api.dian_document_utils.update_doc_with_xml_info",
        args: {
          docname: frm.doc.name
        },
        callback: function(r) {
          if (r.message) {
            frm.reload_doc();
          }
        }
      });
    });
    
    // Create Document button
    frm.add_custom_button("Insert/Update DIAN Tercero from XML", function() {
      if (!frm.doc.xml) {
        frappe.msgprint(__("Please attach an XML first."));
        return;
      }
      frappe.call({
        method: "va_app.va_dian.api.dian_document_utils.update_dian_tercero_with_xml_info",
        args: {
          docname: frm.doc.name
        },
        callback: function(r) {
          if (r.message) {
            frm.reload_doc();
            frappe.msgprint(__("Document should have been updated: ") + r.message);
          }
        }
      });
    });
  }
});

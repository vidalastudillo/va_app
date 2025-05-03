/* -----------------------------------------------------------------------------

Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-04-03

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
      // Add Extract Info button
      frm.add_custom_button("Extract Info", function() {
        if (!frm.doc.xml) {
          frappe.msgprint(__("Please attach an XML first."));
          return;
        }
        frappe.call({
          method: "your_app.api.extract_xml_info",
          args: {
            docname: frm.doc.name
          },
          callback: function(r) {
            if (r.message) {
              frm.reload_doc();
              frappe.msgprint(__("Extraction completed successfully."));
            }
          }
        });
      });
  
      // Add Create Document button
      frm.add_custom_button("Create Document", function() {
        frappe.call({
          method: "your_app.api.create_document",
          args: {
            docname: frm.doc.name
          },
          callback: function(r) {
            if (r.message) {
              frappe.msgprint(__("Document created: ") + r.message);
            }
          }
        });
      });
    }
  });

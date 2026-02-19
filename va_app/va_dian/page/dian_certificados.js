frappe.pages['dian-certificados'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'Certificados Tributarios',
    single_column: true
  });

  const form = new frappe.ui.FieldGroup({
    fields: [
      { fieldname: 'company', label: 'Company', fieldtype: 'Link', options: 'Company', reqd: 1 },
      { fieldname: 'certificate_type', label: 'Tipo de Certificado', fieldtype: 'Select',
        options: 'RET_FUENTE\nRET_IVA\nRET_ICA', reqd: 1 },
      { fieldname: 'from_date', label: 'Desde', fieldtype: 'Date', reqd: 1 },
      { fieldname: 'to_date', label: 'Hasta', fieldtype: 'Date', reqd: 1 }
    ],
    body: page.body
  });

  form.make();

  page.set_primary_action('Generar Certificados', () => {
    const values = form.get_values();
    frappe.call({
      method: 'va_app.va_dian.api.certificados.generate',
      args: values,
      freeze: true,
      callback: () => {
        frappe.msgprint('Certificados generados correctamente.');
      }
    });
  });
};

frappe.ui.form.on('DIAN_Certificado_Config', {
    refresh(frm) {
        frm.add_custom_button(__('Generate Certificates'), () => {
            frappe.prompt(
                [
                    { fieldname: 'from_date', fieldtype: 'Date', reqd: 1 },
                    { fieldname: 'to_date', fieldtype: 'Date', reqd: 1 },
                ],
                (values) => {
                    frappe.call({
                        method: 'va_app.va_dian.api.generation_service.generate_certificados',
                        args: {
                            certificado_config: frm.doc.name,
                            from_date: values.from_date,
                            to_date: values.to_date,
                        },
                    });
                }
            );
        });
    },
});

import frappe
from frappe.model.document import Document

class DIANCertificadoConfig(Document):

    def validate(self):
        if self.certificate_type == "RET_ICA" and not self.municipio:
            frappe.throw("El municipio es obligatorio para certificados ICA.")

        if self.certificate_type != "RET_ICA" and self.municipio:
            frappe.throw("El municipio solo aplica para ICA.")

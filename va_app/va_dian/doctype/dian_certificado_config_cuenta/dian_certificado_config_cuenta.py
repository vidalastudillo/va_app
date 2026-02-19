import frappe
from frappe.model.document import Document

class DIANCertificadoConfigCuenta(Document):

    def validate(self):
        if self.base_account == self.retention_account:
            frappe.throw(
                "La cuenta base y la cuenta de retención no pueden ser la misma."
            )

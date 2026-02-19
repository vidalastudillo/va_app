import frappe
from frappe.model.document import Document

class DIANCertificado(Document):

    def before_save(self):
        if not self.is_new():
            frappe.throw("Los certificados tributarios no pueden ser modificados.")

    def validate(self):
        total_base = sum(d.base_amount for d in self.details)
        total_ret = sum(d.retained_amount for d in self.details)

        if total_base != self.total_base:
            frappe.throw("Total base inconsistente con el detalle.")

        if total_ret != self.total_retained:
            frappe.throw("Total retenido inconsistente con el detalle.")

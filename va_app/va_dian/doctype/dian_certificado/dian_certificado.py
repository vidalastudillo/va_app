import frappe
from frappe.model.document import Document


class DIANCertificado(Document):
    def validate(self):
        self._validate_dates()
        self._validate_totals()

    def _validate_dates(self):
        if self.from_date > self.to_date:
            frappe.throw("From Date cannot be after To Date")

    def _validate_totals(self):
        total = sum(d.retained_amount for d in self.detalles)
        if total != self.total_retention:
            frappe.throw(
                f"Detail total ({total}) does not match certificate total ({self.total_retention})"
            )

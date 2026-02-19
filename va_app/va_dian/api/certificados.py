import frappe
from va_app.va_dian.certificados.generation import generate_certificates

@frappe.whitelist()
def generate(company, from_date, to_date, certificate_type):
    generate_certificates(company, from_date, to_date, certificate_type)
    return {"status": "ok"}

""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-03

!!!
DRAFT!
Not functional
!!!

---------------------------------------------------------------------------- """


import frappe


@frappe.whitelist()
def create_document(docname):
    source_doc = frappe.get_doc("DIAN document", docname)
    if not source_doc.document_type:
        frappe.throw("Document type is missing. Please extract XML information first.")

    new_doc = None
    # Example: Mapping DIAN Factura Electrónica to ERPNext Sales Invoice
    if source_doc.document_type == "Factura Electrónica":
        new_doc = frappe.new_doc("Sales Invoice")
        new_doc.posting_date = source_doc.transaction_date
        new_doc.customer = source_doc.third_party_nit  # Adjust if you need to map to a Customer record
        # Map additional fields as required:
        # new_doc.some_field = source_doc.some_extracted_field
    else:
        frappe.throw("Document type {0} not supported for automatic creation.".format(source_doc.document_type))

    new_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return new_doc.name

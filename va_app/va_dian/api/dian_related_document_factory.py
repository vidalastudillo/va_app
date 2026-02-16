""" ----------------------------------------------------------------------------
Copyright (c) 2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-16
---------------------------------------------------------------------------- """


import frappe
from frappe.utils import getdate


@frappe.whitelist()
def create_related_document(dian_docname: str) -> str:
    """
    Creates a related ERPNext document from the last document
    of the selected type for the DIAN tercero.
    """

    if not dian_docname:
        frappe.throw("DIAN document name is required")

    dian = frappe.get_doc("DIAN document", dian_docname)

    if not dian.xml_dian_tercero:
        frappe.throw("xml_dian_tercero is required")

    if not dian.related_document_type:
        frappe.throw("related_document_type is required")

    tercero = frappe.get_doc("DIAN tercero", dian.xml_dian_tercero)
    nit = tercero.nit

    if not nit:
        frappe.throw("DIAN tercero does not have a NIT")

    doctype = dian.related_document_type

    # ------------------------------------------------------------------
    # Find last document for the tercero and doctype
    # ------------------------------------------------------------------

    source_docname = _find_last_document(doctype, nit, tercero.name)

    if not source_docname:
        frappe.throw(
            f"No existing {doctype} found for DIAN tercero {tercero.name}"
        )

    source_doc = frappe.get_doc(doctype, source_docname)

    # ------------------------------------------------------------------
    # Copy document (unsaved)
    # ------------------------------------------------------------------

    new_doc = frappe.copy_doc(source_doc)
    new_doc.name = None  # Ensure new document

    # ------------------------------------------------------------------
    # Adjust posting date if needed
    # ------------------------------------------------------------------

    if hasattr(new_doc, "posting_date") and dian.xml_issue_date:
        xml_date = getdate(dian.xml_issue_date)
        if new_doc.posting_date != xml_date:
            new_doc.posting_date = xml_date

    # ------------------------------------------------------------------
    # Clear custom_dian_documento if present
    # ------------------------------------------------------------------

    if hasattr(new_doc, "custom_dian_documento"):
        new_doc.custom_dian_documento = None

    # ------------------------------------------------------------------
    # Save new document
    # ------------------------------------------------------------------

    new_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    # ------------------------------------------------------------------
    # Link back to DIAN document
    # ------------------------------------------------------------------

    dian.related_document = new_doc.name
    dian.save(ignore_permissions=True)
    frappe.db.commit()

    return new_doc.name


# -----------------------------------------------------------------------------


def _find_last_document(doctype: str, nit: str, tercero_name: str) -> str | None:
    """
    Returns the name of the most recent document of the given type
    associated with the DIAN tercero.
    """

    filters = {}

    if doctype == "Sales Invoice":
        customer = frappe.get_value(
            "Customer",
            {"tax_id": nit},
            "name",
        )
        if not customer:
            return None
        filters["customer"] = customer

    elif doctype == "Purchase Invoice":
        supplier = frappe.get_value(
            "Supplier",
            {"tax_id": nit},
            "name",
        )
        if not supplier:
            return None
        filters["supplier"] = supplier

    elif doctype == "Journal Entry":
        filters["custom_dian_tercero"] = tercero_name

    else:
        frappe.throw(f"Unsupported related document type: {doctype}")

    result = frappe.get_all(
        doctype,
        filters=filters,
        order_by="creation desc",
        pluck="name",
        limit=1,
    )

    return result[0] if result else None

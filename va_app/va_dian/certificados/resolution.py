import frappe

def resolve_dian_tercero(gl):
    vt = gl.voucher_type
    vn = gl.voucher_no

    doc = frappe.get_doc(vt, vn)

    for field in ("customer", "supplier", "employee", "shareholder"):
        if hasattr(doc, field) and doc.get(field):
            linked = frappe.get_doc(
                doc.meta.get_field(field).options,
                doc.get(field)
            )
            tercero = linked.get("custom_dian_tercero")
            if tercero:
                return tercero

    return None

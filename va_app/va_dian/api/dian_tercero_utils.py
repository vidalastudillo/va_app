""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-04
---------------------------------------------------------------------------- """


import frappe
from va_app.va_dian.api.dian_data_models import (
    VA_DIAN_Tercero,    
)


@frappe.whitelist()
def upsert_dian_tercero(content) -> str | None:
    """
    Insert/Update document in `DIAN tercero` using the content provided.
    content should contain the information as defined on `VA_DIAN_Tercero`
    class.

    Returns:
    - The `docname` of the record iserted.updated on `DIAN tercero`,
      if successful.
    - None, otherwise.
    """

    if content is None:
        frappe.throw("Please provide content")
        return None

    try:
        content_validated = VA_DIAN_Tercero(**content)
    except:
        frappe.throw("The provided content is not valid")
        return None

    # Try to retrieve document
    are_we_inserting = False
    document_tercero = frappe.get_doc("DIAN tercero", content_validated.nit)

    # Document not available? Insertion in required
    if document_tercero.name is None:
        are_we_inserting = True
        document_tercero = frappe.new_doc("DIAN tercero")

    # Common fields to update
    document_tercero.set('razon_social', content_validated.razon_social)
    document_tercero.set('direccion_principal', content_validated.direccion_principal)
    document_tercero.set('codigo_postal', content_validated.codigo_postal)
    document_tercero.set('ciudad_municipio', content_validated.ciudad_municipio)
    document_tercero.set('departamento', content_validated.departamento)
    document_tercero.set('pais', content_validated.pais)
    document_tercero.set('correo_electronico', content_validated.correo_electronico)
    document_tercero.set('telefono_1', content_validated.telefono_1)

    # Final database operations
    if are_we_inserting:
        document_tercero.insert(ignore_permissions=True)
    else:
        document_tercero.save()

    frappe.db.commit()

    return document_tercero.name

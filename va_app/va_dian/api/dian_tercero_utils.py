""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-07
---------------------------------------------------------------------------- """


import frappe
from va_app.va_dian.api.dian_data_models import (
    VA_DIAN_Tercero,    
)


def aux_get_dian_tercero(tercero_id) -> VA_DIAN_Tercero:
    """
    Helper that provides a DIAN tercero object to ease result assignment.
    """

    # Retrive the record on table `DIAN tercero` for the ID
    dian_tercero_records = frappe.db.get_all(
        doctype='DIAN tercero',
        fields=[
            "razon_social",
            "nombre_comercial",
            "primer_apellido",
            "segundo_apellido",
            "primer_nombre",
            "otros_nombres",
            "direccion_principal",
            "ciudad_municipio",
            "departamento",
            "pais",
            "codigo_postal",
            "correo_electronico",
            "telefono_1",
        ],
        filters={"name": tercero_id},
    )

    # Check if there is a valid record returned
    if len(dian_tercero_records)<1:
        # No record, means an empty class is returned.
        return VA_DIAN_Tercero(
            nit=tercero_id,
        )

    # Select a single record from the list
    dian_tercero_record = dian_tercero_records[0]

    # Build the class content to be returned
    to_return = VA_DIAN_Tercero(
        nit=tercero_id,
        razon_social=dian_tercero_record.get('razon_social'),
        nombre_comercial=dian_tercero_record.get('nombre_comercial'),
        primer_apellido=dian_tercero_record.get('primer_apellido'),
        segundo_apellido=dian_tercero_record.get('segundo_apellido'),
        primer_nombre=dian_tercero_record.get('primer_nombre'),
        otros_nombres=dian_tercero_record.get('otros_nombres'),
        direccion_principal=dian_tercero_record.get('direccion_principal'),
        ciudad_municipio=dian_tercero_record.get('ciudad_municipio'),
        departamento=dian_tercero_record.get('departamento'),
        pais=dian_tercero_record.get('pais'),
        codigo_postal=dian_tercero_record.get('codigo_postal'),
        correo_electronico=dian_tercero_record.get('correo_electronico'),
        telefono_1=dian_tercero_record.get('telefono_1'),
    )
    return to_return


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
    try:
        document_tercero = frappe.get_doc("DIAN tercero", content_validated.nit, for_update=True)
    except frappe.exceptions.DoesNotExistError:
        # Document not available? Insertion in required
        are_we_inserting = True
        document_tercero = frappe.new_doc("DIAN tercero")
        document_tercero.set('nit', content_validated.nit)

    # Common fields to update
    document_tercero.set('razon_social', content_validated.razon_social)
    document_tercero.set('direccion_principal', content_validated.direccion_principal)
    document_tercero.set('codigo_postal', content_validated.codigo_postal)
    document_tercero.set('ciudad_municipio', content_validated.ciudad_municipio)
    document_tercero.set('departamento', content_validated.departamento)
    document_tercero.set('pais', content_validated.pais)
    document_tercero.set('correo_electronico', content_validated.correo_electronico)
    document_tercero.set('telefono_1', content_validated.telefono_1)

    # TODO: Update from function
    document_tercero.set('div', 9999)
    document_tercero.set('nombre_completo', content_validated.razon_social)

    # Final database operations
    if are_we_inserting:
        document_tercero.insert(ignore_permissions=True)
    else:
        document_tercero.save()

    frappe.db.commit()

    return document_tercero.name

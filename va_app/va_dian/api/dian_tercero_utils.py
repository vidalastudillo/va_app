""" ----------------------------------------------------------------------------
Copyright (c) 2024-2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-17
---------------------------------------------------------------------------- """


import frappe
from va_app.va_dian.api.dian_data_models import (
    VA_DIAN_Tercero,    
)
from va_app.va.api.erp_fieldnames import (
	UNKNOWN_PARTY,
	DIAN_TERCERO_DOCTYPE_NAME,
	EMPLOYEE_DOCTYPE_NAME,
	EMPLOYEE_FIELD_NAME_DIAN_TERCERO,
	SHAREHOLDER_DOCTYPE_NAME,
	SHAREHOLDER_FIELD_NAME_DIAN_TERCERO,
	CUSTOMER_DOCTYPE_NAME,
	CUSTOMER_FIELD_NAME_DIAN_TERCERO,
	SUPPLIER_DOCTYPE_NAME,
	SUPPLIER_FIELD_NAME_DIAN_TERCERO,
	JOURNAL_FIELD_NAME_DIAN_TERCERO,
	PAYMENT_FIELD_NAME_PARTY_TYPE,
	PAYMENT_FIELD_NAME_PARTY,
	PURCHASE_INVOICE_FIELD_NAME_PARTY,
	PURCHASE_RECEIPT_FIELD_NAME_PARTY,
	SALES_INVOICE_FIELD_NAME_PARTY,
	DELIVERY_NOTE_FIELD_NAME_PARTY,
	STOCK_ENTRY_FIELD_NAME_PARTY,
)


def aux_get_dian_tercero(tercero_id) -> VA_DIAN_Tercero:
    """
    Helper that provides a `DIAN tercero` object to ease result assignment.
	Returns a `DIAN tercero` object:
	- Populated from the `DIAN Tercero` table, if found.
	- Populated with the resto of fields empty, otherwise.
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
		# pluck="name",  # TODO: Not sure if this is required.
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


def aux_get_dian_tercero_id_for_party(
		party_type: str,
		party: str,
	) -> str:
	"""
	Returns the formal NIT from the `DIAN tercero` table for a `party`
	depending on its `party_type`.
	"""

	# Define fields to use to retrieve information from the DocType
	match party_type:
		case '*SpecialCaseTypeDIAN*':
			selected_doctype = DIAN_TERCERO_DOCTYPE_NAME
		case 'Employee':
			selected_doctype = EMPLOYEE_DOCTYPE_NAME
			selected_field_for_party = EMPLOYEE_FIELD_NAME_DIAN_TERCERO
		case 'Shareholder':
			selected_doctype = SHAREHOLDER_DOCTYPE_NAME
			selected_field_for_party = SHAREHOLDER_FIELD_NAME_DIAN_TERCERO
		case 'Customer':
			selected_doctype = CUSTOMER_DOCTYPE_NAME
			selected_field_for_party = CUSTOMER_FIELD_NAME_DIAN_TERCERO
		case 'Supplier':
			selected_doctype = SUPPLIER_DOCTYPE_NAME
			selected_field_for_party = SUPPLIER_FIELD_NAME_DIAN_TERCERO
		case _:
			return UNKNOWN_PARTY

	# Determine the NIT for the Party
	match party_type:
		case '*SpecialCaseTypeDIAN*':
			current_nit = party
		case _:
			current_nit = frappe.db.get_value(selected_doctype, party, selected_field_for_party) or ""
	return current_nit


def aux_get_dian_tercero_id_from_doctype(
		doc_type: str,
		doc_id: str,
	) -> str:
	"""
	Using a DocType identified with the info provided, returns the ID from
    the `DIAN tercero` table.
	"""

	# Values other than None means the Document may have multiple Party Types
	retrieve_party_type_fieldname = None

	match doc_type:
		case 'Journal Entry':
			selected_party_type = '*SpecialCaseTypeDIAN*'
			selected_field_name_for_party = JOURNAL_FIELD_NAME_DIAN_TERCERO
		case 'Payment Entry':
			retrieve_party_type_fieldname = PAYMENT_FIELD_NAME_PARTY_TYPE
			selected_field_name_for_party = PAYMENT_FIELD_NAME_PARTY
		case 'Purchase Invoice':
			selected_party_type = 'Supplier'
			selected_field_name_for_party = PURCHASE_INVOICE_FIELD_NAME_PARTY
		case 'Purchase Receipt':
			selected_party_type = 'Supplier'
			selected_field_name_for_party = PURCHASE_RECEIPT_FIELD_NAME_PARTY
		case 'Sales Invoice':
			selected_party_type = 'Customer'
			selected_field_name_for_party = SALES_INVOICE_FIELD_NAME_PARTY
		case 'Delivery Note':
			selected_party_type = 'Customer'
			selected_field_name_for_party = DELIVERY_NOTE_FIELD_NAME_PARTY
		case 'Stock Entry':
			selected_party_type = 'Supplier'
			selected_field_name_for_party = STOCK_ENTRY_FIELD_NAME_PARTY
		case _:
			return UNKNOWN_PARTY

	# For the cases that the Party Type is yet to be determined
	if retrieve_party_type_fieldname is not None:
		selected_party_type = frappe.db.get_value(doc_type, doc_id, retrieve_party_type_fieldname)

	# Retrieve the Party from the DocType
	selected_party = frappe.db.get_value(doc_type, doc_id, selected_field_name_for_party) or ""

	# Return the ID of the tercero (NIT)
	return aux_get_dian_tercero_id_for_party(
		party_type=selected_party_type,
		party=selected_party,
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

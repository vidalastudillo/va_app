""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-07

* PROMPT USED *

Please consider this related to a custom `Frappe` 15 custom app called `VA DIAN`:

1. I have a DocType called `Terceros`.

2. `Shareholder`, `Employee`, `Customer`, `Supplier` and `Journal Entry` Doctypes each have a `custom field` of type `Link` called `custom_dian_tercero`

Please give me Python server script code that:

1. Summarizes the debits and credits from the `GL Entry` table for a date range grouped by account and my custom field `custom_dian_tercero`
2. Provides the result as a Script Report
3. provides the result as an https API response that receives a date range and returns a JSON

(The solution provided did not worked. Then the following additional prompt lead to a correct solution)

As I have mentioned initially, the `custom_dian_tercero` is a `custom field` of type `Link` on each table `Shareholder`, `Employee`, `Customer`, `Supplier` and `Journal Entry`. Then the `GL Entry` record may use the `Purchase Invoice`, `Sales Invoice`, and others `vouchers` to determine the  `Shareholder`, `Employee`, `Customer`, `Supplier` depending on the case, and from there, the related record on my custom DocType called `Terceros`.
---------------------------------------------------------------------------- """


import frappe
from frappe import _
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


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    # Validate filters
    if not from_date or not to_date:
        frappe.throw(_("Please set both From Date and To Date"))

    # Define report columns
    columns = [
        {
            "fieldname": "account",
            "label": _("Account"),
            "fieldtype": "Link",
            "options":"Account",
            "width": 200
        },
        {
            "fieldname": "total_debit",
            "label": _("Total Debit"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        },
        {
            "fieldname": "total_credit",
            "label": _("Total Credit"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        },
        {
            "fieldname": "total",
            "label": _("Total D-C"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        },
        {
            "fieldname": "tercero_id",
            "label": _("DIAN Tercero"),
            "fieldtype": "Link",
            "options": "DIAN tercero",
            "width": 120
        },
        {
            "fieldname": "tercero_razon_social",
            "label": _("Razón social"),
            "fieldtype": "Text",
            "width": 180
        },
        {
            "fieldname": "tercero_nombre_comercial",
            "label": _("Nombre comercial"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_primer_apellido",
            "label": _("Primer apellido"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_segundo_apellido",
            "label": _("Segundo apellido"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_primer_nombre",
            "label": _("Primer nombre"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_otros_nombres",
            "label": _("Otros nombres"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_direccion_principal",
            "label": _("Dirección principal"),
            "fieldtype": "Text",
            "width": 150
        },
        {
            "fieldname": "tercero_ciudad_municipio",
            "label": _("Ciudad/Municipio"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_departamento",
            "label": _("Departamento"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_pais",
            "label": _("País"),
            "fieldtype": "Text",
            "width": 120
        },
        {
            "fieldname": "tercero_codigo_postal",
            "label": _("Código postal"),
            "fieldtype": "Text",
            "width": 80
        },
        {
            "fieldname": "tercero_correo_electronico",
            "label": _("Correo electrónico"),
            "fieldtype": "Text",
            "width": 150
        },
        {
            "fieldname": "tercero_telefono_1",
            "label": _("Teléfono 1"),
            "fieldtype": "Text",
            "width": 120
        },
    ]

    # Fetch GL Entries in date range
    entries = frappe.db.get_all("GL Entry",
        fields=["account", "party_type", "party", "voucher_type", "voucher_no", "debit", "credit"],
        filters={"posting_date": ["between", [from_date, to_date]]},
        order_by="account",
	)

    # Aggregate by (account, tercero_id)
    summary = {}
    for e in entries:
        account = e.account
        tercero_id = None

        # Resolve tercero_id via party document
        if e.party_type and e.party:
            # e.g. e.party_type = 'Customer', e.party = 'CUST-001'
            tercero_id = frappe.get_value(e.party_type, e.party, "custom_dian_tercero")
            # print(f"GOT value: {tercero_id} from identified fields")
        elif e.voucher_type == "Journal Entry" and e.voucher_no:
            # For Journal Entries, retrieve from Journal Entry record
            tercero_id = frappe.get_value("Journal Entry", e.voucher_no, "custom_dian_tercero")
            # print(f"GOT value: {tercero_id} from Journal")

        # Use None or blank if not found
        tercero_id = tercero_id or ""

        # Key by account and tercero_id
        key = (account, tercero_id)

        # If key is not yet on the records, it is created
        if key not in summary:
            # Detail about the Tercero is populated
            tercero_detail = aux_get_dian_tercero(tercero_id)
            summary[key] = {
                "account": account,
                "tercero_id": tercero_id,
                "tercero_razon_social": tercero_detail.razon_social,
                "tercero_nombre_comercial": tercero_detail.nombre_comercial,
                "tercero_primer_apellido": tercero_detail.primer_apellido,
                "tercero_segundo_apellido": tercero_detail.segundo_apellido,
                "tercero_primer_nombre": tercero_detail.primer_nombre,
                "tercero_otros_nombres": tercero_detail.otros_nombres,
                "tercero_direccion_principal": tercero_detail.direccion_principal,
                "tercero_ciudad_municipio": tercero_detail.ciudad_municipio,
                "tercero_departamento": tercero_detail.departamento,
                "tercero_pais": tercero_detail.pais,
                "tercero_codigo_postal": tercero_detail.codigo_postal,
                "tercero_correo_electronico": tercero_detail.correo_electronico,
                "tercero_telefono_1": tercero_detail.telefono_1,
                "total_debit": 0.0,
                "total_credit": 0.0,
                "total": 0.0,
            }

        summary[key]["total_debit"] += e.debit
        summary[key]["total_credit"] += e.credit
        summary[key]["total"] += (e.debit - e.credit)

    # Prepare data rows
    data = []
    for (acct, terc), vals in summary.items():
        data.append({
            "account": vals.get("account"),
            "tercero_id": vals.get("tercero_id"),
            "tercero_razon_social": vals.get("tercero_razon_social"),
            "tercero_nombre_comercial": vals.get("tercero_nombre_comercial"),
            "tercero_primer_apellido": vals.get("tercero_primer_apellido"),
            "tercero_segundo_apellido": vals.get("tercero_segundo_apellido"),
            "tercero_primer_nombre": vals.get("tercero_primer_nombre"),
            "tercero_otros_nombres": vals.get("tercero_otros_nombres"),
            "tercero_direccion_principal": vals.get("tercero_direccion_principal"),
            "tercero_ciudad_municipio": vals.get("tercero_ciudad_municipio"),
            "tercero_departamento": vals.get("tercero_departamento"),
            "tercero_pais": vals.get("tercero_pais"),
            "tercero_codigo_postal": vals.get("tercero_codigo_postal"),
            "tercero_correo_electronico": vals.get("tercero_correo_electronico"),
            "tercero_telefono_1": vals.get("tercero_telefono_1"),
            "total_debit": round(vals.get("total_debit"), 2) or 0,
            "total_credit": round(vals.get("total_credit"), 2) or 0,
            "total": round(vals.get("total"), 2) or 0
        })

    return columns, data

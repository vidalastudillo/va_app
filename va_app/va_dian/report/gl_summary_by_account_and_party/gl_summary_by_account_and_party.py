""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-09

* PROMPT USED (for the draft of this module) *

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
from va_app.va_dian.api.dian_tercero_utils import (
    aux_get_dian_tercero,
    aux_get_dian_tercero_id_for_party,
    aux_get_dian_tercero_id_from_doctype,
)
# from erpnext.accounts.report.financial_statements import (
# 	compute_growth_view_data,
# 	get_columns,
# 	get_data,
# 	get_filtered_list_for_consolidated_report,
# 	get_period_list,
# )


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    group_by_voucher_type = filters.get("group_by_voucher_type")  # boolean
    show_voucher = filters.get("show_voucher")  # boolean
    use_int_values = filters.get("use_int_values")  # boolean

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
            "width": 200,
        },
        {
            "fieldname": "tercero_id",
            "label": _("DIAN Tercero"),
            "fieldtype": "Link",
            "options": "DIAN tercero",
            "width": 120,
        },
    ]
    # Optional columns
    if group_by_voucher_type:
        columns.append({
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "width": 150,
            # "hidden": 0 if group_by_voucher_type else 1,
        })
    if show_voucher:
        columns.append({
            "label": _("Voucher"),
            "fieldname": "voucher",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",  # Not sure how to make this work
            "width": 150,
        })
    # Remaining required columns
    columns += [
        {
            "fieldname": "total_debit",
            "label": _("Total Debit"),
            "fieldtype": "Text" if use_int_values else "Currency",
            "options": None if use_int_values else "currency",
            "width": 150,
        },
        {
            "fieldname": "total_credit",
            "label": _("Total Credit"),
            "fieldtype": "Text" if use_int_values else "Currency",
            "options": None if use_int_values else "currency",
            "width": 150,
        },
        {
            "fieldname": "total",
            "label": _("Total D-C"),
            "fieldtype": "Text" if use_int_values else "Currency",
            "options": None if use_int_values else "currency",
            "width": 150,
        },
        {
            "fieldname": "tercero_razon_social",
            "label": _("Razón social"),
            "fieldtype": "Text",
            "width": 180,
        },
        {
            "fieldname": "tercero_nombre_comercial",
            "label": _("Nombre comercial"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_primer_apellido",
            "label": _("Primer apellido"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_segundo_apellido",
            "label": _("Segundo apellido"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_primer_nombre",
            "label": _("Primer nombre"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_otros_nombres",
            "label": _("Otros nombres"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_direccion_principal",
            "label": _("Dirección principal"),
            "fieldtype": "Text",
            "width": 150,
        },
        {
            "fieldname": "tercero_ciudad_municipio",
            "label": _("Ciudad/Municipio"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_departamento",
            "label": _("Departamento"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_pais",
            "label": _("País"),
            "fieldtype": "Text",
            "width": 120,
        },
        {
            "fieldname": "tercero_codigo_postal",
            "label": _("Código postal"),
            "fieldtype": "Text",
            "width": 80,
        },
        {
            "fieldname": "tercero_correo_electronico",
            "label": _("Correo electrónico"),
            "fieldtype": "Text",
            "width": 150,
        },
        {
            "fieldname": "tercero_telefono_1",
            "label": _("Teléfono 1"),
            "fieldtype": "Text",
            "width": 120,
        },
    ]

    # Fetch GL Entries in date range
    entries = frappe.db.get_all("GL Entry",
        fields=["account", "party_type", "party", "voucher_type", "voucher_no", "debit", "credit"],
        filters={"posting_date": ["between", [from_date, to_date]]},
        order_by="account, voucher_type, posting_date",
	)

    # We'll use a dict to aggregate the results. Its key is a tuple composed
    # by account, tercero_id, and - optionally - voucher_type and voucher
    data_map = {}
    for e in entries:
        # ######################################################################
        # Preliminar: Determining Tercero Key
        # ######################################################################

        tercero_id = None

        # Resolve tercero_id via party information if present
        if e.party_type and e.party:
            tercero_id = aux_get_dian_tercero_id_for_party(
                party_type=e.party_type,
                party=e.party,
            )
            # print(f"GOT value: {tercero_id} from identified fields")
        elif e.voucher_type and e.voucher_no:
            # For Journal Entries, retrieve from Journal Entry record
            tercero_id = aux_get_dian_tercero_id_from_doctype(
                doc_type=e.voucher_type,
                doc_id=e.voucher_no,
            )
            # print(f"GOT value: {tercero_id} from Document")

        # Use None or blank if not found
        tercero_id = tercero_id or ""

        # ######################################################################
        # Building the Map Key
        # ######################################################################

        # Key by account and tercero_id
        group_key = (e.account, tercero_id)

        # Add voucher_type grouping
        if group_by_voucher_type:
            group_key = (*group_key, e.voucher_type)

        # Add voucher grouping
        if show_voucher:
            group_key = (*group_key, e.voucher_no)

        # ######################################################################
        # Building the Map
        # ######################################################################

        # If key is not yet on the records, it is created
        if group_key not in data_map:
            # Detail about the Tercero is populated
            tercero_detail = aux_get_dian_tercero(tercero_id)
            data_map[group_key] = {
                "account": e.account,
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
            # Append the the optional data
            if group_by_voucher_type:
                data_map[group_key]["voucher_type"] = e.voucher_type
            if show_voucher:
                data_map[group_key]["voucher"] = e.voucher_no

        data_map[group_key]["total_debit"] += e.debit
        data_map[group_key]["total_credit"] += e.credit
        data_map[group_key]["total"] += (e.debit - e.credit)

    # Prepare the data for the report
    data = []
    # Trick to determine the amount of items enumerated on the Map Key
    the_key = ('the_account', 'the_tercero')
    if group_by_voucher_type and show_voucher:
        the_key = ('the_account', 'the_tercero', 'the_voucher_type', 'the_voucher')
    elif group_by_voucher_type:
        the_key = ('the_account', 'the_tercero', 'the_voucher_type')
    elif show_voucher:
        the_key = ('the_account', 'the_tercero', 'the_voucher')

    for the_key, the_values in data_map.items():

        # Values should be rounded and converted into ints if required
        amount_of_decimals = 0 if use_int_values else 2
        total_debit = round(the_values.get("total_debit"), amount_of_decimals) or 0
        total_credit = round(the_values.get("total_credit"), amount_of_decimals) or 0
        total = round(the_values.get("total"), amount_of_decimals) or 0

        if use_int_values:
            total_debit = int(total_debit)
            total_credit = int(total_credit)
            total = int(total)

        data_to_append = {
            "account": the_values.get("account"),
            "tercero_id": the_values.get("tercero_id"),
            "tercero_razon_social": the_values.get("tercero_razon_social"),
            "tercero_nombre_comercial": the_values.get("tercero_nombre_comercial"),
            "tercero_primer_apellido": the_values.get("tercero_primer_apellido"),
            "tercero_segundo_apellido": the_values.get("tercero_segundo_apellido"),
            "tercero_primer_nombre": the_values.get("tercero_primer_nombre"),
            "tercero_otros_nombres": the_values.get("tercero_otros_nombres"),
            "tercero_direccion_principal": the_values.get("tercero_direccion_principal"),
            "tercero_ciudad_municipio": the_values.get("tercero_ciudad_municipio"),
            "tercero_departamento": the_values.get("tercero_departamento"),
            "tercero_pais": the_values.get("tercero_pais"),
            "tercero_codigo_postal": the_values.get("tercero_codigo_postal"),
            "tercero_correo_electronico": the_values.get("tercero_correo_electronico"),
            "tercero_telefono_1": the_values.get("tercero_telefono_1"),
            # Without str format won't be the expected
            "total_debit": str(total_debit),
            "total_credit": str(total_credit),
            "total": str(total),
        }
        # Append optional data
        if group_by_voucher_type:
            data_to_append.update({
                   "voucher_type": _(the_values.get("voucher_type"))
            })
        if show_voucher:
            data_to_append.update({
                   "voucher": the_values.get("voucher")
            })

        data.append(data_to_append)

    return columns, data

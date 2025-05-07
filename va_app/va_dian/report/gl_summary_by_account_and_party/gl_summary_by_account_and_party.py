""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-06

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
            "fieldname": "tercero",
            "label": _("DIAN Tercero"),
            "fieldtype": "Link",
            "options": "DIAN tercero",
            "width": 300
        },
        {
            "fieldname": "total_debit",
            "label": _("Total Debit"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140
        },
        {
            "fieldname": "total_credit",
            "label": _("Total Credit"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140
        },
        {
            "fieldname": "total",
            "label": _("Total D-C"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140
        }
    ]

    # Fetch GL Entries in date range
    entries = frappe.db.get_all("GL Entry",
        fields=["account", "party_type", "party", "voucher_type", "voucher_no", "debit", "credit"],
        filters={"posting_date": ["between", [from_date, to_date]]},
        order_by="account",
	)

    # Aggregate by (account, tercero)
    summary = {}
    for e in entries:
        account = e.account
        tercero = None

        # Resolve tercero via party document
        if e.party_type and e.party:
            # e.g. e.party_type = 'Customer', e.party = 'CUST-001'
            tercero = frappe.get_value(e.party_type, e.party, "custom_dian_tercero")
            # print(f"GOT value: {tercero} from identified fields")
        elif e.voucher_type == "Journal Entry" and e.voucher_no:
            # For Journal Entries, retrieve from Journal Entry record
            tercero = frappe.get_value("Journal Entry", e.voucher_no, "custom_dian_tercero")
            # print(f"GOT value: {tercero} from Journal")

        # Use None or blank if not found
        tercero = tercero or ""

        # Key by account and tercero
        key = (account, tercero)
        if key not in summary:
            summary[key] = {"account": account, "tercero": tercero, "total_debit": 0.0, "total_credit": 0.0, "total": 0.0}
        summary[key]["total_debit"] += e.debit
        summary[key]["total_credit"] += e.credit
        summary[key]["total"] += (e.debit - e.credit)

    # Prepare data rows
    data = []
    for (acct, terc), vals in summary.items():
        data.append({
            "account": vals.get("account"),
            "tercero": vals.get("tercero"),
            "total_debit": vals.get("total_debit") or 0,
            "total_credit": vals.get("total_credit") or 0,
            "total": vals.get("total") or 0
        })

    return columns, data

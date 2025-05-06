""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-06
---------------------------------------------------------------------------- """


from __future__ import unicode_literals
import frappe

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    # Query GL Entries grouped by Account and Party
    entries = frappe.get_all("GL Entry",
        filters={"posting_date": ["between", [from_date, to_date]]},
        fields=[
            "account", "party_type", "party",
            "SUM(debit) as total_debit", 
            "SUM(credit) as total_credit"
        ],
        group_by="account, party_type, party",
        order_by="account, party_type, party"
    )

    # Define report columns
    columns = [
        {"fieldname":"account",    "label":"Account",     "fieldtype":"Link",         "options":"Account"},
        {"fieldname":"party_type", "label":"Party Type",  "fieldtype":"Select",       "options":["Customer","Supplier","Employee","Shareholder"]},
        {"fieldname":"party",      "label":"Party",       "fieldtype":"Dynamic Link","options":"party_type"},
        {"fieldname":"total_debit","label":"Total Debit", "fieldtype":"Currency",      "options":"currency"},
        {"fieldname":"total_credit","label":"Total Credit","fieldtype":"Currency",     "options":"currency"}
    ]

    # Prepare data rows
    data = []
    for row in entries:
        data.append({
            "account": row.get("account"),
            "party_type": row.get("party_type"),
            "party": row.get("party"),
            "total_debit": row.get("total_debit") or 0,
            "total_credit": row.get("total_credit") or 0
        })

    return columns, data

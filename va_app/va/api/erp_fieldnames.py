""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2025-05-07

--------------------------------------------------------------------------------

Field names on ERPNext.

---------------------------------------------------------------------------- """


# Unknowns
UNKNOWN_ACCOUNT = "UNKNOWN_ACCOUNT"
UNKNOWN_PARTY = "UNKNOWN_PARTY"

# Fields on GL Entry Query
GL_ENTRY_FIELD_NAME_ACCOUNTS = "account"
GL_ENTRY_FIELD_NAME_PARTY = "party"
GL_ENTRY_FIELD_NAME_PARTY_TYPE = "party_type"
GL_ENTRY_FIELD_NAME_POSTING_DATE = "posting_date"
GL_ENTRY_FIELD_NAME_VOUCHER_TYPE = "voucher_type"
GL_ENTRY_FIELD_NAME_VOUCHER_SUBTYPE = "voucher_subtype"
GL_ENTRY_FIELD_NAME_VOUCHER_NO = "voucher_no"
GL_ENTRY_FIELD_NAME_CURRENCY = "currency"
GL_ENTRY_FIELD_NAME_OPENING_DEBIT = "opening_debit"
GL_ENTRY_FIELD_NAME_OPENING_CREDIT = "opening_credit"
GL_ENTRY_FIELD_NAME_DEBIT = "debit"
GL_ENTRY_FIELD_NAME_CREDIT = "credit"
GL_ENTRY_FIELD_NAME_CLOSING_DEBIT = "closing_debit"
GL_ENTRY_FIELD_NAME_CLOSING_CREDIT = "closing_credit"

# DIAN tercero
DIAN_TERCERO_DOCTYPE_NAME = "DIAN tercero"
DIAN_TERCERO_FIELD_NAME_NOMBRE_COMPLETO = "nombre_completo"

# Employee
EMPLOYEE_DOCTYPE_NAME = "Employee"
EMPLOYEE_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Shareholder
SHAREHOLDER_DOCTYPE_NAME = "Shareholder"
SHAREHOLDER_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Customer
CUSTOMER_DOCTYPE_NAME = "Customer"
CUSTOMER_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Supplier
SUPPLIER_DOCTYPE_NAME = "Supplier"
SUPPLIER_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Journal fields
JOURNAL_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Payment fields
PAYMENT_FIELD_NAME_PARTY_TYPE = "party_type"
PAYMENT_FIELD_NAME_PARTY = "party"

# Purchase Invoice
PURCHASE_INVOICE_FIELD_NAME_PARTY = "supplier"

# Purchase Receipt
PURCHASE_RECEIPT_FIELD_NAME_PARTY = "supplier"

# Sales Invoice
SALES_INVOICE_FIELD_NAME_PARTY = "customer"

# Delivery Note
DELIVERY_NOTE_FIELD_NAME_PARTY = "customer"

# Stock Entry
STOCK_ENTRY_FIELD_NAME_PARTY = "supplier"

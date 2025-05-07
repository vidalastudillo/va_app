""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-07

!!!
DRAFT!
Not functional
!!!

---------------------------------------------------------------------------- """


import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import add_days, cstr, flt, formatdate, getdate

import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)
from erpnext.accounts.report.financial_statements import (
	filter_accounts,
	filter_out_zero_value_rows,
	set_gl_entries_by_account,
)
from erpnext.accounts.report.utils import convert_to_presentation_currency, get_currency


# This should be off on production
ENABLE_DEVELOPMENT_LOGS = False


# Hard coded definitions
CUSTOM_FIELD_NAME_GROUPING = "grouping"
FIELD_NAME_ACCOUNTS = "account"
FIELD_NAME_PARTY_ON_GL_ENTRY = "party"
FIELD_NAME_PARTY_TYPE_ON_GL_ENTRY = "party_type"
CUSTOM_FIELD_NAME_PARTY_ON_RESULT = "party_selected"
CUSTOM_FIELD_NAME_GL_ENTRY = "gl_entry"
FIELD_NAME_POSTING_DATE = "posting_date"
FIELD_NAME_VOUCHER_TYPE = "voucher_type"
FIELD_NAME_VOUCHER_SUBTYPE = "voucher_subtype"
FIELD_NAME_VOUCHER_NO = "voucher_no"
FIELD_NAME_CURRENCY = "currency"
FIELD_NAME_OPENING_DEBIT = "opening_debit"
FIELD_NAME_OPENING_CREDIT = "opening_credit"
FIELD_NAME_DEBIT = "debit"
FIELD_NAME_CREDIT = "credit"
FIELD_NAME_CLOSING_DEBIT = "closing_debit"
FIELD_NAME_CLOSING_CREDIT = "closing_credit"

PAYMENT_FIELD_NAME_PARTY_TYPE = "party_type"
EMPLOYEE_FIELD_NAME_EMPLOYEE = "employee_name"
SHAREHOLDER_FIELD_NAME_SHAREHOLDER = "title"

UNKNOWN_ACCOUNT = "UNKNOWN_ACCOUNT"
UNKNOWN_PARTY = "UNKNOWN_PARTY"


def execute(filters=None):
	"""
	This function provides the content required by ERPNext for the report.
	"""
	# validate_filters(filters)
	data = get_report_data(filters)
	columns = get_report_columns()
	return columns, data


def get_report_data(filters):
	"""
	Provide the data displayed by the report.
	"""

	# First, we obtain all the GL Entries on the database
	# TODO: Filters are not yet implemented

	order_by_statement = f"""order by {FIELD_NAME_ACCOUNTS}, {FIELD_NAME_POSTING_DATE}, creation"""

	gl_entries = frappe.db.sql(
		f"""
		select
			name as {CUSTOM_FIELD_NAME_GL_ENTRY}, {FIELD_NAME_POSTING_DATE}, {FIELD_NAME_ACCOUNTS}, {FIELD_NAME_PARTY_TYPE_ON_GL_ENTRY}, {FIELD_NAME_PARTY_ON_GL_ENTRY},
			{FIELD_NAME_DEBIT}, {FIELD_NAME_CREDIT},
			{FIELD_NAME_VOUCHER_TYPE}, {FIELD_NAME_VOUCHER_SUBTYPE}, {FIELD_NAME_VOUCHER_NO},
			cost_center, project,
			against_voucher_type, against_voucher, account_currency,
			against, is_opening, creation
		from `tabGL Entry`
		where company=%(company)s
		{order_by_statement}
	""",
		filters,
		as_dict=1,
	)
	if ENABLE_DEVELOPMENT_LOGS:
		frappe.log("GL Entries from the Database")
		frappe.log(gl_entries)

	# The content obtained from the Database is reorganized to match the
	# structure used by the report
	got_form_remap = remap_database_content(
		filters=filters,
		db_results=gl_entries,
	)
	return got_form_remap


def get_report_columns():
	"""
	Provide the columns used by the report.
	"""
	return [
		{
			"fieldname": CUSTOM_FIELD_NAME_GROUPING,
			"label": _("Account and Party on Voucher"),
			"fieldtype": "Data",
			"width": 320,
		},
		{
			"fieldname": CUSTOM_FIELD_NAME_PARTY_ON_RESULT,
			"label": _("Party on Voucher"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": FIELD_NAME_PARTY_ON_GL_ENTRY,
			"label": _("Party on GL"),
			"fieldtype": "Data",
			"width": 150,
			"hidden": 1,
		},
		{
			"fieldname": FIELD_NAME_POSTING_DATE,
			"label": _("Posting Date"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_VOUCHER_TYPE,
			"label": _("Voucher Type"),
			"fieldtype": "Data",
			"width": 200,
			"hidden": 1,
		},
		{
			"fieldname": FIELD_NAME_VOUCHER_SUBTYPE,
			"label": _("Voucher Subtype"),
			"fieldtype": "Data",
			"width": 200,
			"hidden": 1,
		},
		{
			"fieldname": FIELD_NAME_VOUCHER_NO,
			"label": _("Voucher"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 200,
		},
		{
			"fieldname": FIELD_NAME_CURRENCY,
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
		{
			"fieldname": FIELD_NAME_OPENING_DEBIT,
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": FIELD_NAME_OPENING_CREDIT,
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": FIELD_NAME_DEBIT,
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": FIELD_NAME_CREDIT,
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": FIELD_NAME_CLOSING_DEBIT,
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": FIELD_NAME_CLOSING_CREDIT,
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
	]


def remap_database_content(
	filters,
	db_results: dict[object]
) -> list[dict[str, object]] | None:
	"""
	Takes the DB results and reorganizes them to match the required structure
	for the Report which in this case provides a hierarchy that groups the 
	the General Ledger Entries according to:

			`Account : Party` > GL record with data about transactions.

	The Plan:

	We have to return a list of dicts, each containing key pairs consisting of
	field names and values.

	To speed the process, we first use a dict that groups the accounts and
	parties	to store the GL results.

	Once that is completed, we process that dict as a list to return the
	fields requested.
	"""

	# First, we retrieve the accounts
	accounts = frappe.db.sql(
		"""select name, account_number, parent_account, account_name, root_type, report_type, lft, rgt

		from `tabAccount` where company=%s order by lft""",
		filters.company,
		as_dict=True,
	)

	if not accounts:
		return None

	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

	temporal_grouping_dict: dict[str, dict[str, list[str, dict[str, object]]]] = {}

	for single_gl_entry in db_results:

		# Make sure the account key exists on our temporal
		current_account = single_gl_entry.get(FIELD_NAME_ACCOUNTS)
		if current_account is None:
			current_account = UNKNOWN_ACCOUNT
		if current_account not in temporal_grouping_dict:
			temporal_grouping_dict[current_account] = {}

		# Determine the party based on the voucher
		current_voucher_type = single_gl_entry.get(FIELD_NAME_VOUCHER_TYPE)
		current_voucher_no = single_gl_entry.get(FIELD_NAME_VOUCHER_NO)
		current_party_type_from_gl = single_gl_entry.get(FIELD_NAME_PARTY_TYPE_ON_GL_ENTRY)
		current_party_from_gl = single_gl_entry.get(FIELD_NAME_PARTY_ON_GL_ENTRY)

		match current_voucher_type:
			case 'Journal Entry':
				current_selected_party = None
			case 'Payment Entry':

				# Payment Entry uses the field `party` to identify them, but
				# to determine the correct one, we have to discern the `Shareholder` case whose name is a code instead of the proper name as with `Supplier` or `Customers` cases.
				current_party_type_from_payment_entry = frappe.db.get_value(current_voucher_type, current_voucher_no, PAYMENT_FIELD_NAME_PARTY_TYPE)
				current_party_from_payment_entry = frappe.db.get_value(current_voucher_type, current_voucher_no, 'party')
				match current_party_type_from_payment_entry:
					case 'Shareholder':
						current_selected_party = frappe.db.get_value(current_party_type_from_payment_entry, current_party_from_payment_entry, SHAREHOLDER_FIELD_NAME_SHAREHOLDER)
					case _:
						current_selected_party = frappe.db.get_value(current_voucher_type, current_voucher_no, 'party')

			case 'Purchase Invoice':
				current_selected_party = frappe.db.get_value(current_voucher_type, current_voucher_no, 'supplier')
			case 'Purchase Receipt':
				current_selected_party = frappe.db.get_value(current_voucher_type, current_voucher_no, 'supplier')
			case 'Sales Invoice':
				current_selected_party = frappe.db.get_value(current_voucher_type, current_voucher_no, 'customer')
			case 'Delivery Note':
				current_selected_party = frappe.db.get_value(current_voucher_type, current_voucher_no, 'customer')
			case 'Stock Entry':
				current_selected_party = frappe.db.get_value(current_voucher_type, current_voucher_no, 'supplier')
			case _:
				current_selected_party = None

		if current_selected_party is None:
			# Check if the Party fiend on the GL is set
			if current_party_type_from_gl is not None and current_party_from_gl is not None:
				match current_party_type_from_gl:
					case 'Employee':
						current_selected_party = frappe.db.get_value(current_party_type_from_gl, current_party_from_gl, EMPLOYEE_FIELD_NAME_EMPLOYEE)
					case 'Shareholder':
						current_selected_party = frappe.db.get_value(current_party_type_from_gl, current_party_from_gl, SHAREHOLDER_FIELD_NAME_SHAREHOLDER)
					case _:
						current_selected_party = current_party_from_gl
			else:
				current_selected_party = UNKNOWN_PARTY

		# Make sure the party exists on our temporal
		if current_selected_party not in temporal_grouping_dict[current_account]:
			temporal_grouping_dict[current_account][current_selected_party] = []

		# Build the record to append to the dict
		record_constructed = {
			FIELD_NAME_PARTY_ON_GL_ENTRY: single_gl_entry.get(FIELD_NAME_PARTY_ON_GL_ENTRY),
			CUSTOM_FIELD_NAME_GL_ENTRY: single_gl_entry.get(CUSTOM_FIELD_NAME_GL_ENTRY),
			FIELD_NAME_POSTING_DATE: single_gl_entry.get(FIELD_NAME_POSTING_DATE),
			FIELD_NAME_VOUCHER_TYPE: current_voucher_type,
			FIELD_NAME_VOUCHER_NO: current_voucher_no,
			FIELD_NAME_CURRENCY: single_gl_entry.get(FIELD_NAME_CURRENCY),
			FIELD_NAME_OPENING_DEBIT: single_gl_entry.get(FIELD_NAME_OPENING_DEBIT),
			FIELD_NAME_OPENING_CREDIT: single_gl_entry.get(FIELD_NAME_OPENING_CREDIT),
			FIELD_NAME_DEBIT: single_gl_entry.get(FIELD_NAME_DEBIT),
			FIELD_NAME_CREDIT: single_gl_entry.get(FIELD_NAME_CREDIT),
			FIELD_NAME_CLOSING_DEBIT: single_gl_entry.get(FIELD_NAME_CLOSING_DEBIT),
			FIELD_NAME_CLOSING_CREDIT: single_gl_entry.get(FIELD_NAME_CLOSING_CREDIT),
		}

		if ENABLE_DEVELOPMENT_LOGS:
			frappe.log(f"Record to append to account: {current_account} and Party: {current_selected_party}")
			frappe.log(record_constructed)

		# Append the record
		temporal_grouping_dict[current_account][current_selected_party].append(record_constructed)
		if ENABLE_DEVELOPMENT_LOGS:
			frappe.log(f"Current content for account: {current_account} and Party: {current_selected_party}")
			frappe.log(temporal_grouping_dict[current_account][current_selected_party])

	if ENABLE_DEVELOPMENT_LOGS:
		frappe.log("Dict to process")
		frappe.log(temporal_grouping_dict)

	# Process the results to obtain a list
	list_to_return = []
	for single_account_key in temporal_grouping_dict:
		if ENABLE_DEVELOPMENT_LOGS:
			frappe.log("Single Account")
			frappe.log(single_account_key)
		for single_party_key in temporal_grouping_dict[single_account_key]:
			if ENABLE_DEVELOPMENT_LOGS:
				frappe.log("Single party")
				frappe.log(single_party_key)
			for single_gl_entry in temporal_grouping_dict[single_account_key][single_party_key]:

				grouping_field_value = single_account_key + ": " + single_party_key

				single_gl_entry[CUSTOM_FIELD_NAME_GROUPING] = grouping_field_value
				single_gl_entry[CUSTOM_FIELD_NAME_PARTY_ON_RESULT] = single_party_key

				if ENABLE_DEVELOPMENT_LOGS:
					frappe.log("This is the updated GL Entry to append to the resulting list")
					frappe.log(single_gl_entry)
				list_to_return.append(
					single_gl_entry,
				)
	if ENABLE_DEVELOPMENT_LOGS:
		frappe.log("List of dicts")
		frappe.log(list_to_return)

	return list_to_return

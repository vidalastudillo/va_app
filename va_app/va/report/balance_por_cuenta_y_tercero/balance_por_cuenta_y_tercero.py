# Copyright (c) 2024, VIDAL & ASTUDILLO Ltda and contributors
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


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
FIELD_NAME_ACCOUNTS = "account"
FIELD_NAME_PARTY = "party"
FIELD_NAME_GL_ENTRY = "gl_entry"
FIELD_NAME_POSTING_DATE = "posting_date"
FIELD_NAME_VOUCHER_NO = "voucher_no"
FIELD_NAME_CURRENCY = "currency"
FIELD_NAME_OPENING_DEBIT = "opening_debit"
FIELD_NAME_OPENING_CREDIT = "opening_credit"
FIELD_NAME_DEBIT = "debit"
FIELD_NAME_CREDIT = "credit"
FIELD_NAME_CLOSING_DEBIT = "closing_debit"
FIELD_NAME_CLOSING_CREDIT = "closing_credit"
CUSTOM_FIELD_NAME_GROUPING = "grouping"

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

	# We start by obtaining all the GL Entries on the database
	# TODO: Filters are not yet implemented

	order_by_statement = f"""order by {FIELD_NAME_ACCOUNTS}, {FIELD_NAME_POSTING_DATE}, creation"""

	gl_entries = frappe.db.sql(
		f"""
		select
			name as {FIELD_NAME_GL_ENTRY}, {FIELD_NAME_POSTING_DATE}, {FIELD_NAME_ACCOUNTS}, party_type, {FIELD_NAME_PARTY},
			{FIELD_NAME_DEBIT}, {FIELD_NAME_CREDIT},
			voucher_type, voucher_subtype, {FIELD_NAME_VOUCHER_NO},
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
	got_form_remap = remap_database_content(db_results=gl_entries)
	return got_form_remap


def get_report_columns():
	"""
	Provide the columns used by the report.
	"""
	return [
		{
			"fieldname": CUSTOM_FIELD_NAME_GROUPING,
			"label": _("Account and Party"),
			"fieldtype": "Data",
			# "options": "Account",
			"width": 300,
		},
		{
			"fieldname": FIELD_NAME_POSTING_DATE,
			"label": _("Posting Date"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_VOUCHER_NO,
			"label": _("Voucher"),
			"fieldtype": "Data",
			# "options": "Voucher",
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
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_OPENING_CREDIT,
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_DEBIT,
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_CREDIT,
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_CLOSING_DEBIT,
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": FIELD_NAME_CLOSING_CREDIT,
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]


def remap_database_content(db_results: dict[object]) -> list[dict[str, object]]:
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

	temporal_grouping_dict: dict[str, dict[str, list[str, dict[str, object]]]] = {}

	for single_gl_entry in db_results:

		# Make sure the account key exists on our temporal
		current_account = single_gl_entry.get(FIELD_NAME_ACCOUNTS)
		if current_account is None:
			current_account = UNKNOWN_ACCOUNT
		if current_account not in temporal_grouping_dict:
			temporal_grouping_dict[current_account] = {}

		# Make sure the party exists on out temporal
		current_party = single_gl_entry.get(FIELD_NAME_PARTY)
		if current_party is None:
			current_party = UNKNOWN_PARTY
		if current_party not in temporal_grouping_dict[current_account]:
			temporal_grouping_dict[current_account][current_party] = []

		# Build the record to append to the dict
		record_constructed = {
			FIELD_NAME_GL_ENTRY: single_gl_entry.get(FIELD_NAME_GL_ENTRY),
			FIELD_NAME_POSTING_DATE: single_gl_entry.get(FIELD_NAME_POSTING_DATE),
			FIELD_NAME_VOUCHER_NO: single_gl_entry.get(FIELD_NAME_VOUCHER_NO),
			FIELD_NAME_CURRENCY: single_gl_entry.get(FIELD_NAME_CURRENCY),
			FIELD_NAME_OPENING_DEBIT: single_gl_entry.get(FIELD_NAME_OPENING_DEBIT),
			FIELD_NAME_OPENING_CREDIT: single_gl_entry.get(FIELD_NAME_OPENING_CREDIT),
			FIELD_NAME_DEBIT: single_gl_entry.get(FIELD_NAME_DEBIT),
			FIELD_NAME_CREDIT: single_gl_entry.get(FIELD_NAME_CREDIT),
			FIELD_NAME_CLOSING_DEBIT: single_gl_entry.get(FIELD_NAME_CLOSING_DEBIT),
			FIELD_NAME_CLOSING_CREDIT: single_gl_entry.get(FIELD_NAME_CLOSING_CREDIT),
		}

		if ENABLE_DEVELOPMENT_LOGS:
			frappe.log(f"Record to append to account: {current_account} and Party: {current_party}")
			frappe.log(record_constructed)

		# Append the record
		temporal_grouping_dict[current_account][current_party].append(record_constructed)
		if ENABLE_DEVELOPMENT_LOGS:
			frappe.log(f"Current content for account: {current_account} and Party: {current_party}")
			frappe.log(temporal_grouping_dict[current_account][current_party])

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
				grouping_field_value = single_account_key + ":" + single_party_key
				single_gl_entry[CUSTOM_FIELD_NAME_GROUPING] = grouping_field_value
				if ENABLE_DEVELOPMENT_LOGS:
					frappe.log("Tenemos esto para adicionar")
					frappe.log(single_gl_entry)
				list_to_return.append(
					single_gl_entry,
				)
	if ENABLE_DEVELOPMENT_LOGS:
		frappe.log("List of dicts")
		frappe.log(list_to_return)

	return list_to_return

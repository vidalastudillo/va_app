""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-07
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
from va_app.va.api.erp_fieldnames import (
	UNKNOWN_ACCOUNT,
	UNKNOWN_PARTY,
	GL_ENTRY_FIELD_NAME_ACCOUNTS,
	GL_ENTRY_FIELD_NAME_PARTY,
	GL_ENTRY_FIELD_NAME_PARTY_TYPE,
	GL_ENTRY_FIELD_NAME_POSTING_DATE,
	GL_ENTRY_FIELD_NAME_VOUCHER_TYPE,
	GL_ENTRY_FIELD_NAME_VOUCHER_SUBTYPE,
	GL_ENTRY_FIELD_NAME_VOUCHER_NO,
	GL_ENTRY_FIELD_NAME_CURRENCY,
	GL_ENTRY_FIELD_NAME_OPENING_DEBIT,
	GL_ENTRY_FIELD_NAME_OPENING_CREDIT,
	GL_ENTRY_FIELD_NAME_DEBIT,
	GL_ENTRY_FIELD_NAME_CREDIT,
	GL_ENTRY_FIELD_NAME_CLOSING_DEBIT,
	GL_ENTRY_FIELD_NAME_CLOSING_CREDIT,
	DIAN_TERCERO_DOCTYPE_NAME,
	DIAN_TERCERO_FIELD_NAME_NOMBRE_COMPLETO,
)
from va_app.va_dian.api.dian_tercero_utils import (
	aux_get_dian_tercero_id_for_party,
	aux_get_dian_tercero_id_from_doctype,
)


# This should be off on production
ENABLE_DEVELOPMENT_LOGS = False

# Fields on GL Entry Query
CUSTOM_FIELD_NAME_GROUPING = "grouping"
CUSTOM_FIELD_NAME_PARTY_ON_RESULT = "party_selected"
CUSTOM_FIELD_NAME_GL_ENTRY = "gl_entry"


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

	# TODO: Ensure this works
	order_by_statement = f"""order by {GL_ENTRY_FIELD_NAME_POSTING_DATE}, {GL_ENTRY_FIELD_NAME_ACCOUNTS}, creation"""

	gl_entries = frappe.db.sql(
		f"""
		select
			name as {CUSTOM_FIELD_NAME_GL_ENTRY}, {GL_ENTRY_FIELD_NAME_POSTING_DATE}, {GL_ENTRY_FIELD_NAME_ACCOUNTS}, {GL_ENTRY_FIELD_NAME_PARTY_TYPE}, {GL_ENTRY_FIELD_NAME_PARTY},
			{GL_ENTRY_FIELD_NAME_DEBIT}, {GL_ENTRY_FIELD_NAME_CREDIT},
			{GL_ENTRY_FIELD_NAME_VOUCHER_TYPE}, {GL_ENTRY_FIELD_NAME_VOUCHER_SUBTYPE}, {GL_ENTRY_FIELD_NAME_VOUCHER_NO},
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
			"fieldname": GL_ENTRY_FIELD_NAME_PARTY,
			"label": _("Party on GL"),
			"fieldtype": "Data",
			"width": 150,
			"hidden": 1,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_POSTING_DATE,
			"label": _("Posting Date"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_VOUCHER_TYPE,
			"label": _("Voucher Type"),
			"fieldtype": "Data",
			"width": 200,
			"hidden": 1,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_VOUCHER_SUBTYPE,
			"label": _("Voucher Subtype"),
			"fieldtype": "Data",
			"width": 200,
			"hidden": 1,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_VOUCHER_NO,
			"label": _("Voucher"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 200,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_CURRENCY,
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_OPENING_DEBIT,
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_OPENING_CREDIT,
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_DEBIT,
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_CREDIT,
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_CLOSING_DEBIT,
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": GL_ENTRY_FIELD_NAME_CLOSING_CREDIT,
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
	]


def aux_build_dian_tercero_info(
		nit: str,
	) -> str:
	"""
	Returns a string that identifies the party using their formal NIT and
	Full Name from the DIAN tercero table.
	"""

	if nit is None or nit == "":
		return UNKNOWN_PARTY

	# Take the information about that tercero from the DIAN Records
	current_formal_name = frappe.db.get_value(DIAN_TERCERO_DOCTYPE_NAME, nit, DIAN_TERCERO_FIELD_NAME_NOMBRE_COMPLETO) or ""

	joiner = ": "
	current_selected_party = joiner.join([nit, current_formal_name])
	return current_selected_party


def remap_database_content(
	db_results: dict[object],
) -> list[dict[str, object]]:
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

		"""
		Determine content from the current record
		"""

		# Make sure the account key exists on our temporal
		current_account = single_gl_entry.get(GL_ENTRY_FIELD_NAME_ACCOUNTS)
		if current_account is None:
			current_account = UNKNOWN_ACCOUNT
		if current_account not in temporal_grouping_dict:
			temporal_grouping_dict[current_account] = {}

		# Determine the party based on the voucher
		current_voucher_type = single_gl_entry.get(GL_ENTRY_FIELD_NAME_VOUCHER_TYPE)
		current_voucher_no = single_gl_entry.get(GL_ENTRY_FIELD_NAME_VOUCHER_NO)
		current_party_type_from_gl = single_gl_entry.get(GL_ENTRY_FIELD_NAME_PARTY_TYPE)
		current_party_from_gl = single_gl_entry.get(GL_ENTRY_FIELD_NAME_PARTY)

		"""
		Determine the current party
		"""

		# If the party is specified for the record, then it prevails over the
		# document's
		if current_party_type_from_gl is not None \
			and current_party_type_from_gl != '' \
			and current_party_from_gl is not None \
			and current_party_from_gl != '':

			# Get the Tercero ID
			current_nit = aux_get_dian_tercero_id_for_party(
				party_type=current_party_type_from_gl,
				party=current_party_from_gl,
			)

		else:
			# With no direct party on the record, extracts it from the
			# associated Voucher
			current_nit = aux_get_dian_tercero_id_from_doctype(
				doc_type=current_voucher_type,
				doc_id=current_voucher_no,
			)

		# Build a representation for the Tercero ID
		current_selected_party = aux_build_dian_tercero_info(
			nit=current_nit,
		)

		"""
		Insert GL Entry into the result
		"""

		# Make sure the party exists on our temporal
		if current_selected_party not in temporal_grouping_dict[current_account]:
			temporal_grouping_dict[current_account][current_selected_party] = []

		# Build the record to append to the dict
		record_constructed = {
			GL_ENTRY_FIELD_NAME_PARTY: single_gl_entry.get(GL_ENTRY_FIELD_NAME_PARTY),
			CUSTOM_FIELD_NAME_GL_ENTRY: single_gl_entry.get(CUSTOM_FIELD_NAME_GL_ENTRY),
			GL_ENTRY_FIELD_NAME_POSTING_DATE: single_gl_entry.get(GL_ENTRY_FIELD_NAME_POSTING_DATE),
			GL_ENTRY_FIELD_NAME_VOUCHER_TYPE: current_voucher_type,
			GL_ENTRY_FIELD_NAME_VOUCHER_NO: current_voucher_no,
			GL_ENTRY_FIELD_NAME_CURRENCY: single_gl_entry.get(GL_ENTRY_FIELD_NAME_CURRENCY),
			GL_ENTRY_FIELD_NAME_OPENING_DEBIT: single_gl_entry.get(GL_ENTRY_FIELD_NAME_OPENING_DEBIT),
			GL_ENTRY_FIELD_NAME_OPENING_CREDIT: single_gl_entry.get(GL_ENTRY_FIELD_NAME_OPENING_CREDIT),
			GL_ENTRY_FIELD_NAME_DEBIT: single_gl_entry.get(GL_ENTRY_FIELD_NAME_DEBIT),
			GL_ENTRY_FIELD_NAME_CREDIT: single_gl_entry.get(GL_ENTRY_FIELD_NAME_CREDIT),
			GL_ENTRY_FIELD_NAME_CLOSING_DEBIT: single_gl_entry.get(GL_ENTRY_FIELD_NAME_CLOSING_DEBIT),
			GL_ENTRY_FIELD_NAME_CLOSING_CREDIT: single_gl_entry.get(GL_ENTRY_FIELD_NAME_CLOSING_CREDIT),
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

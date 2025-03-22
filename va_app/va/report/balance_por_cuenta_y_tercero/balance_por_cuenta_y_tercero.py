# Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
# 2025-03-21

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


# Fields on GL Entry Query
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

# Unknowns
UNKNOWN_ACCOUNT = "UNKNOWN_ACCOUNT"
UNKNOWN_PARTY = "UNKNOWN_PARTY"

# DIAN tercero
DIAN_TERCERO_DOCTYPE_NAME = "DIAN terceros"
DIAN_TERCERO_FIELD_NAME_NOMBRE_COMPLETO = "nombre_completo"

# Employee
EMPLOYEE_DOCTYPE_NAME = "Employee"
EMPLOYEE_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"
EMPLOYEE_FIELD_NAME_EMPLOYEE = "employee_name"

# Shareholder
SHAREHOLDER_DOCTYPE_NAME = "Shareholder"
SHAREHOLDER_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"
SHAREHOLDER_FIELD_NAME_SHAREHOLDER = "title"

# Customer
CUSTOMER_DOCTYPE_NAME = "Customer"
CUSTOMER_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Supplier
SUPPLIER_DOCTYPE_NAME = "Supplier"
SUPPLIER_FIELD_NAME_DIAN_TERCERO = "custom_dian_tercero"

# Journal fields
JOURNAL_FIELD_NAME_DIAN_TERCERO = "custom_tercero_dian"  # Cambiar una vez resuelto nombre definitivo

# Payment fields
PAYMENT_FIELD_NAME_PARTY_TYPE = "party_type"


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




def aux_build_dian_tercero_info(
		nit: str,
	) -> str:
	"""
	Returns a string that identifies the party using their formal NIT and
	Full Name from the DIAN terceros table.
	"""

	# Take the information about that tercero from the DIAN Records
	current_formal_name = frappe.db.get_value(DIAN_TERCERO_DOCTYPE_NAME, nit, DIAN_TERCERO_FIELD_NAME_NOMBRE_COMPLETO) or ""

	joiner = ": "
	current_selected_party = joiner.join([nit, current_formal_name])
	return current_selected_party


def aux_get_dian_tercero_info_for_party_type(
		party_type: str,
		party: str,
	) -> str:
	"""
	Returns a string that identifies the party using their formal NIT and
	Full Name from the DIAN terceros table.
	"""

	match party_type:
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

	# Take the ID of the tercero (NIT) and use it to retrive its info
	current_nit = frappe.db.get_value(selected_doctype, party, selected_field_for_party) or ""
	current_selected_party = aux_build_dian_tercero_info(
		nit=current_nit,
	)
	return current_selected_party


def aux_get_dian_tercero_info_from_doctype(
		doc_type: str,
		doc_id: str,
		field_name_for_party: str,
	) -> str:
	"""
	Using a DocType identified with the info provided, returns a string
	that identifies the party using their formal NIT and Full Name whose
	data is retrieved from the DIAN terceros table.
	"""

	# Take the ID of the tercero (NIT)
	current_nit = frappe.db.get_value(doc_type, doc_id, field_name_for_party) or ""
	current_selected_party = aux_build_dian_tercero_info(
		nit=current_nit,
	)
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

		"""
		Determine the current party
		"""

		# If the party is specified for the record, then it prevail over the
		# document's
		if current_party_type_from_gl is not None \
			and current_party_type_from_gl != '' \
			and current_party_from_gl is not None \
			and current_party_from_gl != '':

			current_selected_party = aux_get_dian_tercero_info_for_party_type(
				party_type=current_party_type_from_gl,
				party=current_party_from_gl,
			)

		else:

			match current_voucher_type:

				case 'Journal Entry':
					current_selected_party = aux_get_dian_tercero_info_from_doctype(
						doc_type=current_voucher_type,
						doc_id=current_voucher_no,
						field_name_for_party=JOURNAL_FIELD_NAME_DIAN_TERCERO,
					)

				case 'Payment Entry':

					# Payment Entry uses the field `party` to identify them, but the content of that field needs to be evaluated depending on the `Party type`
					# to differentiate the codes used by `Employee` and `Shareholder` as opposed to the complete names used by the other types.
					current_party_type_from_payment_entry = frappe.db.get_value(current_voucher_type, current_voucher_no, PAYMENT_FIELD_NAME_PARTY_TYPE)
					current_party_from_payment_entry = frappe.db.get_value(current_voucher_type, current_voucher_no, 'party')

					match current_party_type_from_payment_entry:
						case 'Employee':
							current_selected_party = frappe.db.get_value(current_party_type_from_payment_entry, current_party_from_payment_entry, EMPLOYEE_FIELD_NAME_EMPLOYEE)
						case 'Shareholder':
							current_selected_party = frappe.db.get_value(current_party_type_from_payment_entry, current_party_from_payment_entry, SHAREHOLDER_FIELD_NAME_SHAREHOLDER)
						case _:  # Supplier and Customer use their name instead of a code
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

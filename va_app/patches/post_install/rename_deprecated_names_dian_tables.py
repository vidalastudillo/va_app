""" ----------------------------------------------------------------------------
Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2025-05-03
---------------------------------------------------------------------------- """

import frappe


def execute():
	# frappe.db.sql(
	# 	"""UPDATE `tabPrint Format`
	# 	SET module = 'Payroll'
	# 	WHERE name IN ('Salary Slip Based On Timesheet', 'Salary Slip Standard')"""
	# )

	try:
		frappe.get_doc('DocType', 'DIAN terceros')
	except frappe.exceptions.DoesNotExistError:
		print("'DIAN terceros' not need to be renamed")
	else:
		frappe.db.rename_table("DIAN terceros", "DIAN tercero")
		print(f"'DIAN terceros' ranaming processed")
	
	try:
		frappe.get_doc('DocType', 'tabDIAN documents')
	except frappe.exceptions.DoesNotExistError:
		print(f"'DIAN documents' not need to be renamed")
	else:
		frappe.db.rename_table("DIAN documents", "DIAN document")
		print(f"'DIAN documents' ranaming processed")
	
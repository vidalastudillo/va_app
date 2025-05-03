""" ----------------------------------------------------------------------------
Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
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
		# frappe.get_doc('DocType', 'tabDIAN terceros')
		frappe.db.rename_table("tabDIAN terceros", "tabDIAN tercero")
	# except frappe.exceptions.DoesNotExistError:
	except Exception as exception:
		print(f"'tabDIAN terceros' not renamed: {exception}")
	else:
		print(f"'tabDIAN terceros' ranaming processed")
	
	try:
		# frappe.get_doc('DocType', 'tabDIAN documents')
		frappe.db.rename_table("tabDIAN documents", "tabDIAN document")
	# except frappe.exceptions.DoesNotExistError:
	except Exception as exception:
		print(f"'tabDIAN documents' not renamed: {exception}")
	else:
		print(f"'tabDIAN documents' ranaming processed")
	
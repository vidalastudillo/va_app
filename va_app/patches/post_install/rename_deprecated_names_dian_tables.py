# Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors
# For license information, please see license.txt
# By JMVA, VIDAL & ASTUDILLO Ltda
# Version 2025-05-03


import frappe


def execute():
	# frappe.db.sql(
	# 	"""UPDATE `tabPrint Format`
	# 	SET module = 'Payroll'
	# 	WHERE name IN ('Salary Slip Based On Timesheet', 'Salary Slip Standard')"""
	# )

	frappe.db.rename_table("tabDIAN terceros", "tabDIAN tercero")
	frappe.db.rename_table("tabDIAN documents", "tabDIAN document")

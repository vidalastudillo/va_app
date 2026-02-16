/* -----------------------------------------------------------------------------

Copyright (c) 2025, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2025-05-09

----------------------------------------------------------------------------- */


frappe.query_reports["GL Summary by Account and Party"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"reqd":1 
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"reqd":1
		},
		{
			"fieldname": "group_by_voucher_type",
			"label": "Group by Voucher Type",
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_voucher",
			"label": "Show voucher",
			"fieldtype": "Check",
		},
		{
			"fieldname": "use_int_values",
			"label": "Use integer values",
			"fieldtype": "Check",
		}
	]
};
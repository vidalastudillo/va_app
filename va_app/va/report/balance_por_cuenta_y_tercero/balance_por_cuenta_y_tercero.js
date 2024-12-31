// Copyright (c) 2024, VIDAL & ASTUDILLO Ltda and contributors
// For license information, please see license.txt

frappe.query_reports["Balance por cuenta y tercero"] = {
	"filters": [
		{
			"label": "Account",
        		"fieldname": "account",
          		"fieldtype": "Link",
			"options":'Account',
           		"width": 200,
			"reqd": 1
		}
	]
};

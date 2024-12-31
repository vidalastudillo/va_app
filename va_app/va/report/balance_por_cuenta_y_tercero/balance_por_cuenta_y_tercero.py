# Copyright (c) 2024, VIDAL & ASTUDILLO Ltda and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = [{"fieldname": "make", "label": "Make", "fieldtype": "Data", "width": 150}]
    data = [{"make": "BMW"}, {"make": "Subaru"}]
    return columns, data
 
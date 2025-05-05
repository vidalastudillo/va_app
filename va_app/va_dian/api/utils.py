""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-04

--------------------------------------------------------------------------------

Utils.

---------------------------------------------------------------------------- """


import json
import frappe


@frappe.whitelist()
def provide_nicely_formatted_dictionary(dictionary) -> str:
    """
    Provides a dictionary with idented structure
    """
    return json.dumps(dictionary, indent=4)

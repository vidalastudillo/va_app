""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-04

--------------------------------------------------------------------------------

Utils.

---------------------------------------------------------------------------- """


import frappe


@frappe.whitelist()
def provide_nicely_formatted_dictionary(data: dict, indent=0) -> str:
    """
    Provides a dictionary with idented structure
    """

    result = ""
    for key, value in data.items():
        result += " " * indent + str(key) + ": "
        if isinstance(value, dict):
            result += "\n" + provide_nicely_formatted_dictionary(value, indent + 4)
        elif isinstance(value, list):
             result += "[" + ",".join(map(str, value)) + "]\n"
        else:
            result += str(value) + "\n"
    return result

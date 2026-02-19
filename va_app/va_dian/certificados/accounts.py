import frappe

def expand_account(account_name: str) -> list[str]:
    acc = frappe.get_doc("Account", account_name)
    if not acc.is_group:
        return [acc.name]

    children = frappe.get_all(
        "Account",
        filters={"lft": (">", acc.lft), "rgt": ("<", acc.rgt), "is_group": 0},
        pluck="name",
    )
    return children

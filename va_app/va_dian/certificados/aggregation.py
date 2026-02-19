import frappe
from .accounts import expand_account
from .resolution import resolve_dian_tercero

def aggregate(company, from_date, to_date, config):
    results = {}

    for row in config.accounts:
        base_accounts = expand_account(row.base_account)
        ret_accounts = expand_account(row.retention_account)

        gls = frappe.get_all(
            "GL Entry",
            filters={
                "company": company,
                "posting_date": ["between", [from_date, to_date]],
                "account": ["in", base_accounts + ret_accounts],
                "is_cancelled": 0,
            },
            fields=["*"],
        )

        for gl in gls:
            tercero = resolve_dian_tercero(gl)
            if not tercero:
                continue

            key = (tercero, row.base_account, row.retention_account)
            results.setdefault(key, {"base": 0, "ret": 0})

            amount = gl.debit - gl.credit
            if gl.account in base_accounts:
                results[key]["base"] += amount
            elif gl.account in ret_accounts:
                results[key]["ret"] += amount

    return results

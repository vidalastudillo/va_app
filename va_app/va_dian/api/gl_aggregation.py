import frappe
from collections import defaultdict
from typing import Dict, List


PARTY_DOCTYPES = {
    "Customer": "Customer",
    "Supplier": "Supplier",
    "Employee": "Employee",
    "Shareholder": "Shareholder",
}


def resolve_dian_tercero(party_type: str, party: str) -> str | None:
    if party_type not in PARTY_DOCTYPES:
        return None

    return frappe.db.get_value(
        PARTY_DOCTYPES[party_type],
        party,
        "custom_dian_tercero",
    )


def aggregate_retention_details(
    account: str,
    from_date: str,
    to_date: str,
) -> Dict[str, List[dict]]:
    """
    Returns:
    {
      "DIAN-TER-0001": [
        {
          "retention_account": "23654001",
          "concepto": "Retención en la fuente",
          "base_amount": 0,
          "retained_amount": 125000
        }
      ]
    }
    """

    rows = frappe.db.sql(
        """
        SELECT
            party_type,
            party,
            account,
            SUM(debit - credit) AS retained
        FROM `tabGL Entry`
        WHERE
            account = %s
            AND posting_date BETWEEN %s AND %s
            AND party IS NOT NULL
            AND is_cancelled = 0
        GROUP BY party_type, party, account
        """,
        (account, from_date, to_date),
        as_dict=True,
    )

    results = defaultdict(list)

    for row in rows:
        dian_tercero = resolve_dian_tercero(row.party_type, row.party)
        if not dian_tercero:
            continue

        retained = abs(row.retained)
        if not retained:
            continue

        results[dian_tercero].append(
            {
                "retention_account": row.account,
                "concepto": frappe.db.get_value(
                    "Account", row.account, "account_name"
                ),
                "base_amount": 0,
                "retained_amount": retained,
            }
        )

    return dict(results)

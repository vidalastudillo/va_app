import frappe
from va_app.va_dian.api.gl_aggregation import aggregate_retention_details


def find_existing_certificado(
    certificado_config: str,
    dian_tercero: str,
    from_date: str,
    to_date: str,
) -> str | None:
    return frappe.db.get_value(
        "DIAN_Certificado",
        {
            "certificado_config": certificado_config,
            "dian_tercero": dian_tercero,
            "from_date": from_date,
            "to_date": to_date,
        },
        "name",
    )


@frappe.whitelist()
def generate_certificados(
    certificado_config: str,
    from_date: str,
    to_date: str,
) -> dict:
    """
    Idempotent certificate generation.

    Returns:
        {
          "created": [...],
          "updated": [...]
        }
    """

    config = frappe.get_doc("DIAN_Certificado_Config", certificado_config)

    data = aggregate_retention_details(
        account=config.retention_account,
        from_date=from_date,
        to_date=to_date,
    )

    result = {"created": [], "updated": []}

    for dian_tercero, detalles in data.items():
        total = sum(d["retained_amount"] for d in detalles)

        existing = find_existing_certificado(
            certificado_config=config.name,
            dian_tercero=dian_tercero,
            from_date=from_date,
            to_date=to_date,
        )

        if existing:
            cert = frappe.get_doc("DIAN_Certificado", existing)

            # Replace details atomically
            cert.detalles = []
            for d in detalles:
                cert.append("detalles", d)

            cert.total_retention = total
            cert.save()

            result["updated"].append(cert.name)
        else:
            cert = frappe.get_doc(
                {
                    "doctype": "DIAN_Certificado",
                    "certificado_config": config.name,
                    "dian_tercero": dian_tercero,
                    "from_date": from_date,
                    "to_date": to_date,
                    "total_retention": total,
                    "detalles": detalles,
                }
            )
            cert.insert()
            result["created"].append(cert.name)

    return result

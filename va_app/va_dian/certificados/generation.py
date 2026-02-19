import frappe
from .aggregation import aggregate

def generate_certificates(company, from_date, to_date, certificate_type):
    configs = frappe.get_all(
        "DIAN_CertificadoConfig",
        filters={"company": company, "certificate_type": certificate_type},
        fields=["name"]
    )

    for cfg in configs:
        config = frappe.get_doc("DIAN_CertificadoConfig", cfg.name)
        data = aggregate(company, from_date, to_date, config)

        grouped = {}
        for (tercero, base_acc, ret_acc), vals in data.items():
            grouped.setdefault(tercero, []).append((base_acc, ret_acc, vals))

        for tercero, rows in grouped.items():
            if frappe.db.exists(
                "DIAN_Certificado",
                {
                    "company": company,
                    "certificate_type": certificate_type,
                    "dian_tercero": tercero,
                    "from_date": from_date,
                    "to_date": to_date,
                },
            ):
                continue

            cert = frappe.new_doc("DIAN_Certificado")
            cert.company = company
            cert.certificate_type = certificate_type
            cert.dian_tercero = tercero
            cert.from_date = from_date
            cert.to_date = to_date
            cert.year = from_date.year
            cert.municipio = config.municipio

            total_base = total_ret = 0

            for base_acc, ret_acc, vals in rows:
                cert.append("details", {
                    "base_account": base_acc,
                    "retention_account": ret_acc,
                    "base_amount": vals["base"],
                    "retained_amount": vals["ret"],
                    "config_reference": config.name,
                })
                total_base += vals["base"]
                total_ret += vals["ret"]

            cert.total_base = total_base
            cert.total_retained = total_ret
            cert.insert()

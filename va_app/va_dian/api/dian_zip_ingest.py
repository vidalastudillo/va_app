""" ----------------------------------------------------------------------------
Copyright (c) 2026, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2026-02-15

--------------------------------------------------------------------------------

DIAN Electronic document ingestion.

---------------------------------------------------------------------------- """


import os
import zipfile
import tempfile
import shutil
from pathlib import Path

import frappe
from frappe.utils.file_manager import save_file
from frappe.utils import getdate


@frappe.whitelist()
def ingest_dian_zip(
    file_url: str,
) -> str:
    """
    Receives a ZIP file uploaded to ERPNext, extracts XML + PDF,
    renames files, and creates a new DIAN document.

    Returns:
        The name of the newly created DIAN document
    """

    if not file_url:
        frappe.throw("file_url is required")

    # ------------------------------------------------------------------
    # Locate uploaded ZIP file
    # ------------------------------------------------------------------
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    zip_path = file_doc.get_full_path()

    if not zipfile.is_zipfile(zip_path):
        frappe.throw("Provided file is not a valid ZIP file")

    # ------------------------------------------------------------------
    # Prepare temp workspace
    # ------------------------------------------------------------------
    tmp_dir = tempfile.mkdtemp(prefix="dian_zip_")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        xml_path, pdf_path = _find_xml_and_pdf(tmp_dir)

        # ------------------------------------------------------------
        # Create DIAN document (empty)
        # ------------------------------------------------------------
        # ------------------------------------------------------------------
        # Create DIAN document
        # ------------------------------------------------------------------
        dian_doc = frappe.new_doc("DIAN document")
        dian_doc.insert(ignore_permissions=True)

        # ------------------------------------------------------------------
        # Attach XML
        # ------------------------------------------------------------------
        with open(xml_path, "rb") as f:
            xml_attach = save_file(
                fname=Path(xml_path).name,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                fieldname="xml",
                is_private=1,
            )

        # ------------------------------------------------------------------
        # Attach PDF
        # ------------------------------------------------------------------
        with open(pdf_path, "rb") as f:
            pdf_attach = save_file(
                fname=Path(pdf_path).name,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                fieldname="representation",
                is_private=1,
            )

        dian_doc.save(ignore_permissions=True)
        frappe.db.commit()

        # ------------------------------------------------------------
        # SINGLE SOURCE OF TRUTH: extract XML info
        # ------------------------------------------------------------
        from va_app.va_dian.api.dian_document_utils import update_doc_with_xml_info
        update_doc_with_xml_info(dian_doc.name)

        # Reload with extracted values
        dian_doc.reload()

        # ------------------------------------------------------------
        # Rename attached files using extracted data
        # ------------------------------------------------------------
        _rename_attachments(dian_doc)

        frappe.db.commit()
        return dian_doc.name

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _find_xml_and_pdf(base_dir: str) -> tuple[str, str]:
    xml = pdf = None
    for root, _, files in os.walk(base_dir):
        for f in files:
            lf = f.lower()
            full = os.path.join(root, f)
            if lf.endswith(".xml") and not xml:
                xml = full
            elif lf.endswith(".pdf") and not pdf:
                pdf = full

    if not xml:
        frappe.throw("ZIP does not contain an XML file")
    if not pdf:
        frappe.throw("ZIP does not contain a PDF file")

    return xml, pdf


def _rename_attachments(doc):
    """
    Renames XML and PDF based on extracted party + date.
    """

    if not doc.xml or not doc.representation:
        return

    party = doc.xml_dian_tercero or "Desconocido"

    # Issue date should already be parsed into xml_content by your utils
    issue_date = _extract_issue_date_from_xml_content(doc.xml_content)
    date_prefix = getdate(issue_date).strftime("%y-%m-%d")

    for field in ("xml", "representation"):
        file_doc = frappe.get_doc("File", {"file_url": getattr(doc, field)})
        original = Path(file_doc.file_name)

        new_name = (
            f"{date_prefix} {party} - "
            f"{_sanitize(original.stem)}{original.suffix}"
        )

        file_doc.file_name = new_name
        file_doc.save(ignore_permissions=True)


def _extract_issue_date_from_xml_content(xml_text: str) -> str:
    """
    Minimal, safe extraction — relies on update_doc_with_xml_info
    having already populated xml_content.
    """
    import re
    match = re.search(r"<cbc:IssueDate>(.*?)</cbc:IssueDate>", xml_text)
    if not match:
        frappe.throw("IssueDate not found in extracted XML content")
    return match.group(1)


def _sanitize(name: str) -> str:
    """
    Removes unsafe characters but preserves most of the original filename.
    """
    keep = " ._-"
    return "".join(c for c in name if c.isalnum() or c in keep).strip()

""" ----------------------------------------------------------------------------
Copyright (c) 2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
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


@frappe.whitelist()
def ingest_dian_zip(
    file_url: str,
) -> str:
    """
    Receives a ZIP file uploaded to ERPNext, extracts XML + PDF,
    creates a DIAN document, and triggers post-processing.

    Returns:
        The name of the newly created DIAN document
    """

    if not file_url:
        frappe.throw("file_url is required")

    # ------------------------------------------------------------------
    # Locate uploaded ZIP file.
    # ------------------------------------------------------------------
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    zip_path = file_doc.get_full_path()

    if not zipfile.is_zipfile(zip_path):
        frappe.throw("Provided file is not a valid ZIP file")

    # ------------------------------------------------------------------
    # Prepare temp workspace.
    # ------------------------------------------------------------------
    tmp_dir = tempfile.mkdtemp(prefix="dian_zip_")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        xml_path, pdf_path = _find_xml_and_pdf(tmp_dir)

        # ------------------------------------------------------------------
        # Create DIAN document.
        # ------------------------------------------------------------------
        dian_doc = frappe.new_doc("DIAN document")
        dian_doc.insert(ignore_permissions=True)

        # ------------------------------------------------------------------
        # Attach XML.
        # ------------------------------------------------------------------
        with open(xml_path, "rb") as f:
            save_file(
                fname=Path(xml_path).name,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                fieldname="xml",
                is_private=1,
            )

        # ------------------------------------------------------------------
        # Attach PDF.
        # ------------------------------------------------------------------
        with open(pdf_path, "rb") as f:
            save_file(
                fname=Path(pdf_path).name,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                fieldname="representation",
                is_private=1,
            )

        # ------------------------------------------------------------------
        # XML enrichment.
        # ------------------------------------------------------------------
        from va_app.va_dian.api.dian_document_utils import update_doc_with_xml_info
        update_doc_with_xml_info(dian_doc.name)

        return dian_doc.name

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


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

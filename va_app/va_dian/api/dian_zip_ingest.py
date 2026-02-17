""" ----------------------------------------------------------------------------
Copyright (c) 2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-17

--------------------------------------------------------------------------------

DIAN Electronic document ingestion.

---------------------------------------------------------------------------- """


import os
import re
import zipfile
import tempfile
import shutil
from pathlib import Path

import frappe
from frappe.utils.file_manager import save_file

from va_app.va_dian.api.dian_document_utils import extract_minimal_xml_metadata


MAX_STEM_LEN = 80


@frappe.whitelist()
def ingest_dian_zip(
    file_url: str,
) -> str:
    """
    Receives a ZIP file uploaded to ERPNext, extracts XML + PDF,
    creates a DIAN document attaching renamed files.

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

        # --------------------------------------------------------------
        # Extract metadata BEFORE saving files
        # --------------------------------------------------------------
        meta = extract_minimal_xml_metadata(xml_path)

        if not meta.issue_date or not meta.party_id:
            frappe.throw("XML does not contain required metadata")

        xml_filename = build_final_filename(
            issue_date=meta.issue_date,
            party=meta.party_id,
            original_path=xml_path,
        )

        pdf_filename = build_final_filename(
            issue_date=meta.issue_date,
            party=meta.party_id,
            original_path=pdf_path,
        )

        # --------------------------------------------------------------
        # Create DIAN document.
        # --------------------------------------------------------------
        dian_doc = frappe.new_doc("DIAN document")
        dian_doc.insert(ignore_permissions=True)

        # --------------------------------------------------------------
        # Attach XML.
        # --------------------------------------------------------------
        with open(xml_path, "rb") as f:
            xml_file = save_file(
                fname=xml_filename,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                is_private=1,
            )
            dian_doc.xml = xml_file.file_url

        # --------------------------------------------------------------
        # Attach PDF.
        # --------------------------------------------------------------
        with open(pdf_path, "rb") as f:
            pdf_file = save_file(
                fname=pdf_filename,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                is_private=1,
            )
            dian_doc.representation = pdf_file.file_url

        dian_doc.save(ignore_permissions=True)

        return dian_doc.name

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


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


def _sanitize_filename_part(value: str) -> str:
    """
    Keep only filesystem-safe characters.
    """
    value = value.strip()
    value = re.sub(r"[^\w\s.\-]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value)
    return value


def build_final_filename(
    issue_date,
    party: str,
    original_path: str,
) -> str:
    """
    Build filename according to:
    <Issue Date> <Party> <Original filename truncated>.<ext>
    """
    original = Path(original_path)

    safe_stem = _sanitize_filename_part(original.stem)
    safe_stem = safe_stem[:MAX_STEM_LEN]

    date_prefix = issue_date.strftime("%y-%m-%d")
    party = _sanitize_filename_part(party)

    return f"{date_prefix} {party} - {safe_stem}{original.suffix.lower()}"

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
from datetime import datetime

import frappe
from frappe.utils.file_manager import save_file

from va_app.va_dian.api.dian_document_utils import aux_extract_xml_info
from va_app.va_dian.api.dian_document_utils import aux_get_text
import xml.etree.ElementTree as ET


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

        # ------------------------------------------------------------------
        # Locate XML and PDF
        # ------------------------------------------------------------------
        xml_file = None
        pdf_file = None

        for root, _, files in os.walk(tmp_dir):
            for f in files:
                lf = f.lower()
                full_path = os.path.join(root, f)
                if lf.endswith(".xml") and xml_file is None:
                    xml_file = full_path
                elif lf.endswith(".pdf") and pdf_file is None:
                    pdf_file = full_path

        if not xml_file:
            frappe.throw("No XML file found in ZIP")
        if not pdf_file:
            frappe.throw("No PDF file found in ZIP")

        # ------------------------------------------------------------------
        # Extract party name & issue date directly from XML
        # (lightweight parse, before DIAN document exists)
        # ------------------------------------------------------------------
        party_name, issue_date = _extract_basic_xml_info(xml_file)

        if not party_name or not issue_date:
            frappe.throw("Unable to extract party name or issue date from XML")

        date_obj = datetime.strptime(issue_date, "%Y-%m-%d")
        date_prefix = date_obj.strftime("%y-%m-%d")

        # ------------------------------------------------------------------
        # Build renamed filenames
        # ------------------------------------------------------------------
        xml_original = Path(xml_file).name
        pdf_original = Path(pdf_file).name

        base_xml_name = _sanitize_filename(xml_original)
        base_pdf_name = _sanitize_filename(pdf_original)

        new_xml_name = f"{date_prefix} {party_name} - {base_xml_name}"
        new_pdf_name = f"{date_prefix} {party_name} - {base_pdf_name}"

        # ------------------------------------------------------------------
        # Create DIAN document
        # ------------------------------------------------------------------
        dian_doc = frappe.new_doc("DIAN document")
        dian_doc.insert(ignore_permissions=True)

        # ------------------------------------------------------------------
        # Attach XML
        # ------------------------------------------------------------------
        with open(xml_file, "rb") as f:
            xml_attach = save_file(
                fname=new_xml_name,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                fieldname="xml",
                is_private=1,
            )

        # ------------------------------------------------------------------
        # Attach PDF
        # ------------------------------------------------------------------
        with open(pdf_file, "rb") as f:
            pdf_attach = save_file(
                fname=new_pdf_name,
                content=f.read(),
                dt="DIAN document",
                dn=dian_doc.name,
                fieldname="representation",
                is_private=1,
            )

        dian_doc.save(ignore_permissions=True)
        frappe.db.commit()

        # ------------------------------------------------------------------
        # Reuse your existing logic to extract & enrich data
        # ------------------------------------------------------------------
        from va_app.va_dian.api.dian_document_utils import update_doc_with_xml_info
        update_doc_with_xml_info(dian_doc.name)

        return dian_doc.name

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _extract_basic_xml_info(xml_path: str) -> tuple[str | None, str | None]:
    """
    Extracts:
    - Sender party name
    - Issue date
    Without requiring a DIAN document record.
    """

    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    }

    party_elem = root.find(
        'cac:SenderParty/cac:PartyTaxScheme/cbc:RegistrationName', ns
    )
    date_elem = root.find('cbc:IssueDate', ns)

    party_name = aux_get_text(party_elem)
    issue_date = aux_get_text(date_elem)

    return party_name, issue_date


def _sanitize_filename(name: str) -> str:
    """
    Removes unsafe characters but preserves most of the original filename.
    """
    keep = " ._-"
    return "".join(c for c in name if c.isalnum() or c in keep).strip()

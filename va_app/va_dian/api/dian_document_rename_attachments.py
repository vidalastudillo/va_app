""" ----------------------------------------------------------------------------
Copyright (c) 2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-17
-----------------------------------------------------------------------------

Safe renaming of `DIAN document` attachments.

- Works in Frappe v15 and should do it in v16 (not tested yet).
- Does NOT rename File.name (hash).
- Renames file on disk + updates file_url atomically.
- Safe to run more than onece for the same document (idempotent).

---------------------------------------------------------------------------- """

import os
from pathlib import Path

import frappe
from frappe.utils import getdate


MAX_BASENAME_LEN = 80  # conservative, filesystem-safe


@frappe.whitelist()
def rename_dian_attachments(docname: str):
    """
    Renames XML and PDF attachments of a DIAN document safely.

    Naming convention:
        <YY-MM-DD> <Party> <Original name truncated>.<ext>
    """

    doc = frappe.get_doc("DIAN document", docname)

    if not doc.xml_dian_tercero or not doc.xml_issue_date:
        frappe.throw(
            "No es posible renombrar los archivos: "
            "falta DIAN Tercero y/o Fecha de emisión.",
        )

    date_prefix = getdate(doc.xml_issue_date).strftime("%y-%m-%d")
    party = doc.xml_dian_tercero

    for field in ("xml", "representation"):
        file_url = getattr(doc, field)
        if not file_url:
            continue

        _rename_single_file(
            file_url=file_url,
            date_prefix=date_prefix,
            party=party,
        )


# -----------------------------------------------------------------------------


def _rename_single_file(file_url: str, date_prefix: str, party: str):
    """
    Performs a safe, atomic rename of a File:
    - rename file on disk
    - update file_url and file_name
    """

    file_doc = frappe.get_doc("File", {"file_url": file_url})

    old_path = Path(file_doc.get_full_path())
    if not old_path.exists():
        frappe.log_error(
            f"File not found on disk: {old_path}",
            "DIAN attachment rename",
        )
        return

    original = Path(file_doc.file_name)

    safe_stem = _sanitize(original.stem)[:MAX_BASENAME_LEN]

    new_filename = (
        f"{date_prefix} {party} {safe_stem}{original.suffix}"
    )

    # Already renamed → skip (idempotent)
    if file_doc.file_name == new_filename:
        return

    new_path = old_path.with_name(new_filename)

    # Prevent overwriting existing files
    if new_path.exists():
        frappe.log_error(
            f"Target file already exists: {new_path}",
            "DIAN attachment rename",
        )
        return

    # ------------------------------------------------------------------
    # ATOMIC rename (filesystem + DB)
    # ------------------------------------------------------------------

    os.rename(old_path, new_path)

    file_doc.file_name = new_filename
    file_doc.file_url = file_doc.file_url.replace(
        original.name,
        new_filename,
    )

    file_doc.save(ignore_permissions=True)


# -----------------------------------------------------------------------------


def _sanitize(name: str) -> str:
    """
    Removes unsafe characters while preserving readability.
    """
    keep = " ._-"
    return "".join(c for c in name if c.isalnum() or c in keep).strip()

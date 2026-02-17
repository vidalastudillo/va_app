""" ----------------------------------------------------------------------------
Copyright (c) 2025–2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-17
---------------------------------------------------------------------------- """

from pathlib import Path

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


MAX_FILENAME_LENGTH = 140  # safe across filesystems


class DIANdocument(Document):

    def on_update(self):
        """
        After saving a DIAN document, rename its attached files
        based on XML content (idempotent).
        """
        self.rename_attached_documents_per_xml_content()

    # ---------------------------------------------------------------------

    def rename_attached_documents_per_xml_content(self):
        """
        Rename attached XML / PDF files to:

        <YY-MM-DD> <Party> <Original filename truncated>.<ext>

        Safe for Frappe v15 and v16.
        Does nothing if already renamed.
        """

        party = self.xml_dian_tercero
        issue_date = self.xml_issue_date

        if not party or not issue_date:
            return  # silently skip, no side effects

        date_prefix = getdate(issue_date).strftime("%y-%m-%d")

        for fieldname in ("xml", "representation"):
            file_url = getattr(self, fieldname)
            if not file_url:
                continue

            file_doc = frappe.get_doc("File", {"file_url": file_url})
            original = Path(file_doc.file_name)

            sanitized_stem = self._sanitize(original.stem)
            new_filename = f"{date_prefix} {party} {sanitized_stem}{original.suffix}"

            new_filename = self._truncate_filename(new_filename)

            # Idempotency check: already renamed → do nothing
            if file_doc.file_name == new_filename:
                continue

            # Rename the File *document* (this renames the physical file too)
            frappe.rename_doc(
                "File",
                file_doc.name,
                new_filename,
                force=True,
            )

    # ---------------------------------------------------------------------

    @staticmethod
    def _sanitize(name: str) -> str:
        keep = " ._-"
        return "".join(c for c in name if c.isalnum() or c in keep).strip()

    @staticmethod
    def _truncate_filename(filename: str) -> str:
        """
        Ensure filename length stays within safe limits
        while preserving extension.
        """
        p = Path(filename)
        ext = p.suffix
        max_stem_len = MAX_FILENAME_LENGTH - len(ext)

        if len(p.stem) <= max_stem_len:
            return filename

        return f"{p.stem[:max_stem_len].rstrip()}{ext}"

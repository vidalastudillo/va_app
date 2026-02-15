""" ----------------------------------------------------------------------------
Copyright (c) 2025-2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-15
---------------------------------------------------------------------------- """


import re
from pathlib import Path

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class DIANdocument(Document):

	def before_save(self):
		"""
		Enforce CUFE uniqueness once it exists.
		"""
		if self.cufe:
			existing = frappe.db.exists(
				"DIAN document",
				{
					"cufe": self.cufe,
					"name": ["!=", self.name],
				},
			)
			if existing:
				self.status = "Duplicate"
				frappe.throw(
					f"DIAN document with CUFE {self.cufe} already exists: {existing}"
				)

    # ------------------------------------------------------------------

	def after_insert(self):
		"""
		Finalize processing after XML enrichment.
		"""
		try:
			if self.xml and self.representation and self.xml_content:
				self._rename_attachments()
				self.status = "Processed"
				self.save(ignore_permissions=True)
		except Exception:
			self.status = "Error"
			self.save(ignore_permissions=True)
			raise

    # ------------------------------------------------------------------

	def _rename_attachments(self):
		"""
		Renames XML and PDF using extracted party and issue date.
		"""
		party = self.xml_dian_tercero or "Desconocido"
		issue_date = self._extract_issue_date_from_xml_content()
		date_prefix = getdate(issue_date).strftime("%y-%m-%d")

		for field in ("xml", "representation"):
			file_doc = frappe.get_doc("File", {"file_url": getattr(self, field)})
			original = Path(file_doc.file_name)

			new_name = (
				f"{date_prefix} {party} - "
				f"{self._sanitize(original.stem)}{original.suffix}"
			)

			file_doc.file_name = new_name
			file_doc.save(ignore_permissions=True)

    # ------------------------------------------------------------------

	def _extract_issue_date_from_xml_content(self) -> str:
		"""
		Relies on the result of `update_doc_with_xml_info` which
		produces the content for the field `xml_content`.
		"""
		match = re.search(
			r"<cbc:IssueDate>(.*?)</cbc:IssueDate>",
			self.xml_content or "",
		)
		if not match:
			frappe.throw("IssueDate not found in extracted XML content")
		return match.group(1)

    # ------------------------------------------------------------------

	@staticmethod
	def _sanitize(name: str) -> str:
		keep = " ._-"
		return "".join(c for c in name if c.isalnum() or c in keep).strip()

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
		# frappe.msgprint("DIANdocument before_save controller is running")
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
		Initial state after creation.
		"""
		# frappe.msgprint("DIANdocument after_insert controller is running")
		if not self.status:
			self.status = "Draft"

	# ------------------------------------------------------------------

	def on_update(self):
		"""
		Finalize processing once XML enrichment is complete.
		This runs AFTER `update_doc_with_xml_info`.
		"""
		# frappe.msgprint("DIANdocument on_update controller is running")
		if self.status == "Processed":
			return

		if not (self.xml and self.representation and self.xml_content):
			return

		try:
			self._rename_attachments()
			self.status = "Processed"
			self.db_update()
		except Exception:
			self.status = "Error"
			self.db_update()
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

			if file_doc.file_name != new_name:
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

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

	def after_insert(self):
		"""
		After inserting a `DIAN document`, if there is an attached XML file,
		the related files will be renamed with content of the XML.
		"""

		if self.xml:
			self.rename_attached_documents_per_xml_content()

	def rename_attached_documents_per_xml_content(self):
		"""
		Rename the Electronic Documents attached according to the content
		extracted from the XML (Issue Date Party).
		"""

		party = self.xml_dian_tercero
		issue_date = self.xml_issue_date

		if not party:
			frappe.throw("Tercero DIAN no determinado; No es posible renombrar los archivos adjuntos")

		if not issue_date:
			frappe.throw("Fecha de emisión no determinada; No es posible renombrar los archivos adjuntos")

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

	@staticmethod
	def _sanitize(name: str) -> str:
		keep = " ._-"
		return "".join(c for c in name if c.isalnum() or c in keep).strip()

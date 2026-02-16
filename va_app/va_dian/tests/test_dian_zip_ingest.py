""" ----------------------------------------------------------------------------
Copyright (c) 2026, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2026-02-15
---------------------------------------------------------------------------- """


import frappe
import os

from frappe.tests.utils import FrappeTestCase


class TestDIANZipIngest(FrappeTestCase):

    def setUp(self):
        self.test_zip = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "sample_dian.zip",
        )

    def test_ingestion_creates_processed_document(self):
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": "sample_dian.zip",
            "content": open(self.test_zip, "rb").read(),
            "is_private": 1,
        }).insert()

        from va_app.va_dian.api.dian_zip_ingest import ingest_dian_zip
        name = ingest_dian_zip(file_doc.file_url)

        doc = frappe.get_doc("DIAN document", name)

        self.assertTrue(doc.xml)
        self.assertTrue(doc.representation)
        self.assertTrue(doc.xml_content)
        self.assertTrue(doc.xml_cufe)
        self.assertTrue(doc.xml_dian_tercero)

    def test_duplicate_cufe_is_rejected(self):
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": "sample_dian.zip",
            "content": open(self.test_zip, "rb").read(),
            "is_private": 1,
        }).insert()

        from va_app.va_dian.api.dian_zip_ingest import ingest_dian_zip

        ingest_dian_zip(file_doc.file_url)

        with self.assertRaises(frappe.ValidationError):
            ingest_dian_zip(file_doc.file_url)

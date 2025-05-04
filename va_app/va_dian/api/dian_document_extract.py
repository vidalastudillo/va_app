""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-04

!!!
DRAFT!
Not functional
!!!

---------------------------------------------------------------------------- """


import frappe
import xml.etree.ElementTree as ET
from frappe.utils.file_manager import get_file_path


@frappe.whitelist()
def extract_xml_info(docname):

    document_namespace = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'cdt': 'urn:DocumentInformation:names:specification:ubl:colombia:schema:xsd:DocumentInformationAggregateComponents-1',
        'chl': 'urn:carvajal:names:specification:ubl:colombia:schema:xsd:CarvajalHealthComponents-1',
        'clm54217': 'urn:un:unece:uncefact:codelist:specification:54217:2001',
        'clm66411': 'urn:un:unece:uncefact:codelist:specification:66411:2001',
        'clmIANAMIMEMediaType': 'urn:un:unece:uncefact:codelist:specification:IANAMIMEMediaType:2003',
        'cts': 'urn:carvajal:names:specification:ubl:colombia:schema:xsd:CarvajalAggregateComponents-1',
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'grl': 'urn:General:names:specification:ubl:colombia:schema:xsd:GeneralAggregateComponents-1',
        'ipt': 'urn:DocumentInformation:names:specification:ubl:colombia:schema:xsd:InteroperabilidadPT-1',
        'qdt': 'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2',
        'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
        'udt': 'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2',
        'xades': 'http://uri.etsi.org/01903/v1.3.2#',
        'xades141': 'http://uri.etsi.org/01903/v1.4.1#',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

    document_attachments = []

    doc = frappe.get_doc("DIAN document", docname)
    if not doc.xml:
        frappe.throw("No XML attachment found.")

    # Get the file record
    file_list = frappe.get_all("File", filters={"attached_to_doctype": "DIAN document", "attached_to_name": docname, "file_url": ("like", "%xml%")}, fields=["name", "file_name"])
    if not file_list:
        frappe.throw("Unable to locate the attached XML file.")
    file_doc = file_list[0]

    # Determine the file path.
    file_path = get_file_path(file_doc.file_name)

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for document in root.findall('cac:Attachment', document_namespace):
            for child in document.findall('cac:ExternalReference', document_namespace):
                attachment = child.find('cbc:Description', document_namespace).text
                tr = ET.XML(attachment)
                for b in tr:
                    document_attachments.append(b.text)

        # # Extract info based on your XML structure:
        # doc.document_type = root.findtext("DocumentType") or ""
        # doc.transaction_date = root.findtext("Date") or ""
        # doc.third_party_nit = root.findtext("ThirdParty/NIT") or ""
        # doc.address = root.findtext("ThirdParty/Address") or ""
        # doc.city = root.findtext("ThirdParty/City") or ""
        # doc.postal_code = root.findtext("ThirdParty/PostalCode") or ""
        # # Add other extractions as needed, e.g., transaction details
        # # doc.some_field = root.findtext("Transaction/SomeField") or ""

        document_type = document_attachments.get("AttachedDocument", {}).get("DocumentType", {})
        document_issue_date = document_attachments.get("AttachedDocument", {}).get("IssueDate", {})
        document_issue_time = document_attachments.get("AttachedDocument", {}).get("IssueTime", {})
        doc_sender_party_name = ""
        doc_sender_party_id = ""
        doc_sender_party_id_type = ""
        doc_receiver_party = ""
        doc_item = ""

        match document_type:
            case 'Contenedor de Factura Electrónica':
                doc_sender_party_name = document_attachments.get("AttachedDocument", {}).get("SenderParty", {}).get("PartyTaxScheme", {}).get("RegistrationName", {})
                doc_sender_party_id = document_attachments.get("AttachedDocument", {}).get("SenderParty", {}).get("PartyTaxScheme", {}).get("CompanyID", {}).get("#text", {})
                doc_sender_party_id_type = document_attachments.get("AttachedDocument", {}).get("SenderParty", {}).get("PartyTaxScheme", {}).get("CompanyID", {}).get("@schemeName", {})
                doc_receiver_party = document_attachments.get("AttachedDocument", {}).get("ReceiverParty", {}).get("PartyTaxScheme", {}).get("RegistrationName", {})
                # doc_item = root.findall('Invoice/cac:InvoiceLine/Item')
                # doc_item = root.findall('AttachedDocument/cbc:DocumentType', document_namespace)
                doc_item = root.findall('AttachedDocument/DocumentType', document_namespace)
                

        print("Tenemos esto en contenido")
        print(document_attachments)
        print("Campos de interés identificados")
        print(document_type)
        print(document_issue_date)
        print(document_issue_time)
        print(doc_sender_party_name)
        print(doc_sender_party_id)
        print(doc_sender_party_id_type)
        print(doc_receiver_party)
        print(doc_item)

        # doc.save(ignore_permissions=True)
        return {
            "document_type": doc.document_type,
            "transaction_date": doc.transaction_date,
            "third_party_nit": doc.third_party_nit
        }
    except Exception as e:
        frappe.throw("Error processing XML: " + str(e))

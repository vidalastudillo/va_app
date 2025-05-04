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
import re


@frappe.whitelist()
def extract_xml_info(docname):

    document_namespace = {
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
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
    except Exception as e:
        frappe.throw("Error processing XML: " + str(e))
        return None
    else:

        # Helper to get text or None if missing
        def get_text(elem):
            return elem.text if elem is not None else None

        # ######################################################################
        # Find generic information
        # ######################################################################

        # 1. Extract from root AttachedDocument
        reg_document_type = root.find('cbc:DocumentType', document_namespace)
        document_type = get_text(reg_document_type)

        reg_issue_date = root.find('cbc:IssueDate', document_namespace)
        document_issue_date = get_text(reg_issue_date)

        reg_issue_time = root.find('cbc:IssueTime', document_namespace)
        document_issue_time = get_text(reg_issue_time)

        reg_sender_party_name = root.find('cac:SenderParty/cac:PartyTaxScheme/cbc:RegistrationName', document_namespace)
        document_sender_party_name = get_text(reg_sender_party_name)

        reg_sender_party_id = root.find('cac:SenderParty/cac:PartyTaxScheme/cbc:CompanyID', document_namespace)
        document_sender_party_id = get_text(reg_sender_party_id)

        reg_receiver_party_name = root.find('cac:ReceiverParty/cac:PartyTaxScheme/cbc:RegistrationName', document_namespace)
        document_receiver_party_name = get_text(reg_receiver_party_name)

        reg_receiver_party_id = root.find('cac:ReceiverParty/cac:PartyTaxScheme/cbc:CompanyID', document_namespace)
        document_receiver_party_id = get_text(reg_receiver_party_id)

        # 2. Extract MIME and Encoding from Attachment/ExternalReference
        mime_elem = root.find('cac:Attachment/cac:ExternalReference/cbc:MimeCode', document_namespace)
        enc_elem  = root.find('cac:Attachment/cac:ExternalReference/cbc:EncodingCode', document_namespace)
        mime_code = get_text(mime_elem)
        encoding_code = get_text(enc_elem)

        # 3. Extract the embedded Document XML from the CDATA in Description
        documento_uuid = None
        desc_elem = root.find('cac:Attachment/cac:ExternalReference/cbc:Description', document_namespace)
        if desc_elem is not None and desc_elem.text:
            cdata_text = desc_elem.text.strip()
            try:
                # Parse the CDATA content as XML
                invoice_root = ET.fromstring(cdata_text)
                # The embedded Document uses the same cbc namespace, so reuse ns
                uuid_elem = invoice_root.find('.//cbc:UUID', document_namespace)
                documento_uuid = get_text(uuid_elem)
            except ET.ParseError:
                documento_uuid = None

        # match document_type:
        #     case 'Contenedor de Factura Electrónica':
        # doc_item = root.findall('Invoice/cac:InvoiceLine/Item')
        # doc_item = root.findall('AttachedDocument/cbc:DocumentType', document_namespace)
        # doc_item = root.findall('AttachedDocument/DocumentType', document_namespace)
        
        # Find the Description element that contains the CDATA invoice XML
        desc_elem = root.find('cac:Attachment/cac:ExternalReference/cbc:Description', document_namespace)
        if desc_elem is None or not desc_elem.text:
            raise ValueError("Could not find embedded invoice in the AttachedDocument")
        invoice_xml = desc_elem.text.strip()

        # Remove XML declaration if present
        invoice_xml = re.sub(r'^\\s*<\\?xml[^>]+>', '', invoice_xml)

        # Parse the embedded Invoice XML
        invoice_root = ET.fromstring(invoice_xml)

        # Extract sender address line
        sender_address = invoice_root.findtext(
            'cac:AccountingSupplierParty/cac:Party/cac:PhysicalLocation/cac:Address/cac:AddressLine/cbc:Line',
            namespaces=document_namespace
        ) or ""

        print("Campos de interés identificados")
        print(document_type)
        print(document_issue_date)
        print(document_issue_time)
        print(document_sender_party_name)
        print(document_sender_party_id)
        print(document_receiver_party_name)
        print(document_receiver_party_id)
        print(sender_address)
        print(documento_uuid)
        print(mime_code)
        print(encoding_code)
        print("FIN de campos de interés identificados")

        # doc.save(ignore_permissions=True)
        return {
            "document_type": doc.document_type,
            "transaction_date": doc.transaction_date,
            "third_party_nit": doc.third_party_nit
        }

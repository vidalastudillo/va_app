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
from frappe.utils.file_manager import get_file_path
import xml.etree.ElementTree as ET
from va_app.va_dian.api.dian_data_models import VA_DIAN_Document, VA_DIAN_Address, VA_DIAN_Item


@frappe.whitelist()
def extract_xml_info(docname) -> dict[str, str] | None:
    """
    Provides a dictionary with information contained on the XML document
    """

    # Check requested DIAN Document exists
    doc = frappe.get_doc("DIAN document", docname)
    if not doc.xml:
        frappe.throw("No XML attachment found.")
        return None

    # Get the XML path record
    file_list = frappe.get_all("File", filters={"attached_to_doctype": "DIAN document", "attached_to_name": docname, "file_url": ("like", "%xml%")}, fields=["name", "file_name"])
    if not file_list:
        frappe.throw("Unable to locate the attached XML file.")
    file_doc = file_list[0]

    # Determine the file path.
    file_path = get_file_path(file_doc.file_name)

    # Read the XML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        frappe.throw("Error processing XML: " + str(e))
        return None
    else:

        document_namespace = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        }

        # Helper to get text or None if missing
        def get_text(elem):
            return elem.text.strip() if elem is not None and elem.text else None

        # ######################################################################
        # Find generic information that should be present in any kind of
        # electronic document
        # ######################################################################

        document_type = get_text(root.find('cbc:DocumentType', document_namespace))
        reg_issue_date = root.find('cbc:IssueDate', document_namespace)
        reg_issue_time = root.find('cbc:IssueTime', document_namespace)
        reg_sender_party_name = root.find('cac:SenderParty/cac:PartyTaxScheme/cbc:RegistrationName', document_namespace)
        reg_sender_party_id = root.find('cac:SenderParty/cac:PartyTaxScheme/cbc:CompanyID', document_namespace)
        reg_receiver_party_name = root.find('cac:ReceiverParty/cac:PartyTaxScheme/cbc:RegistrationName', document_namespace)
        reg_receiver_party_id = root.find('cac:ReceiverParty/cac:PartyTaxScheme/cbc:CompanyID', document_namespace)

        # ######################################################################
        # Find document type dependant information
        # ######################################################################

        document_uuid = None
        document_items = None  # Not all documents use this
        document_sender_address = None

        # Find the Description element that contains the CDATA invoice XML
        desc_elem = root.find('cac:Attachment/cac:ExternalReference/cbc:Description', document_namespace)
        if desc_elem is None or not desc_elem.text:
            frappe.throw("Could not find embedded data in the AttachedDocument of the XML")
            return None
        else:
            cdata = desc_elem.text.strip()
            # strip XML declaration if present
            if cdata.startswith('<?xml'):
                cdata = cdata.split('?>', 1)[1]

            try:
                # Parse the CDATA content as XML
                extra_document_root = ET.fromstring(cdata)

                # 1. The embedded Document uses the same cbc namespace, so reuse document_namespace
                document_uuid = get_text(extra_document_root.find('.//cbc:UUID', document_namespace))

                # 2. Sender address
                reg_sender_address_elem = extra_document_root.find('cac:AccountingSupplierParty/cac:Party/cac:PhysicalLocation/cac:Address', document_namespace)
                if reg_sender_address_elem is not None:
                    document_sender_address = VA_DIAN_Address(
                        street_name=get_text(reg_sender_address_elem.find('cac:AddressLine/cbc:Line', document_namespace)),
                        city_name=get_text(reg_sender_address_elem.find('cbc:CityName', document_namespace)),
                        postal_zone=get_text(reg_sender_address_elem.find('cbc:PostalZone', document_namespace)),
                        country=get_text(reg_sender_address_elem.find('cac:Country/cbc:Name', document_namespace)),
                    )

                # 3. Dependant on type of document
                match document_type:
                    case 'Contenedor de Factura Electrónica':
                        # Extract item list
                        for line in extra_document_root.findall('.//cac:InvoiceLine', document_namespace):
                            line_quantity = get_text(line.find('.//cbc:InvoicedQuantity', document_namespace))
                            line_price = get_text(line.find('.//cac:Price/cbc:PriceAmount', document_namespace))
                            line_extension_amount = get_text(line.find('.//cbc:LineExtensionAmount', document_namespace))
                            line_taxable_amount = get_text(line.find('.//cbc:TaxableAmount', document_namespace))
                            line_tax_amount = get_text(line.find('.//cbc:TaxAmount', document_namespace))
                            line_description = get_text(line.find('.//cac:Item/cbc:Description', document_namespace))
                            if document_items is None:
                                document_items = []
                            document_items.append(VA_DIAN_Item(
                                quantity=line_quantity,
                                price=line_price,
                                taxable_amount=line_taxable_amount,
                                tax_amount=line_tax_amount,
                                extension_amount=line_extension_amount,
                                description=line_description,
                            ))
                    case _:
                        frappe.throw("Unknown document type. No extra information would be produced.")

            except ET.ParseError:
                pass

        # Build object
        to_return = VA_DIAN_Document(
            document_type = document_type,
            uuid = document_uuid,
            issue_date = get_text(reg_issue_date),
            issue_time = get_text(reg_issue_time),
            sender_party_name = get_text(reg_sender_party_name),
            sender_party_id = get_text(reg_sender_party_id),
            sender_address = document_sender_address,
            receiver_party_name = get_text(reg_receiver_party_name),
            receiver_party_id = get_text(reg_receiver_party_id),
            items=document_items,
        )

        print("Campos de interés identificados")
        print(to_return)        
        print("FIN de campos de interés identificados")

        return to_return.dict()

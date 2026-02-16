""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors.
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda.
Version 2025-05-07

--------------------------------------------------------------------------------

Data models.

---------------------------------------------------------------------------- """


from enum import StrEnum
from dataclasses import dataclass, field

from va_app.va_dian.api.utils import provide_nicely_formatted_dictionary, recursive_dataclass_to_dict


class ElectronicDocument(StrEnum):
    """
    Tipos de documentos electrónicos implementados en ERPNext
    """
    INDETERMINADO = "Indeterminado"
    FACTURA_ELECTRONICA = "Factura electrónica"


@dataclass
class VA_DIAN_Tercero:
    """Information about a DIAN Tercero"""

    nit: str
    numero_de_identificacion: str | None = field(default=None)
    tipo_de_documento: str | None = field(default=None)
    tipo_de_contribuyente: str | None = field(default=None)
    primer_apellido: str | None = field(default=None)
    segundo_apellido: str | None = field(default=None)
    primer_nombre: str | None = field(default=None)
    otros_nombres: str | None = field(default=None)
    razon_social: str | None = field(default=None)
    nombre_comercial: str | None = field(default=None)
    correo_electronico: str | None = field(default=None)
    telefono_1: str | None = field(default=None)
    telefono_2: str | None = field(default=None)
    direccion_principal: str | None = field(default=None)
    ciudad_municipio: str | None = field(default=None)
    departamento: str | None = field(default=None)
    codigo_postal: str | None = field(default=None)
    pais: str | None = field(default=None)

    def dict(self):
        """
        JSON serializable objects are required when Frappe returns them as
        responses.
        """
        return recursive_dataclass_to_dict(self)


@dataclass
class VA_DIAN_Address:
    """Information about a DIAN Address"""

    direccion: str | None
    ciudad: str | None
    departamento: str | None
    codigo_postal: str | None
    pais: str | None

    def dict(self):
        """
        JSON serializable objects are required when Frappe returns them as
        responses.
        """
        return recursive_dataclass_to_dict(self)


@dataclass
class VA_DIAN_Item:
    """Information about a DIAN Item"""

    quantity: str | None
    price: str | None
    taxable_amount: str | None
    tax_amount: str | None
    extension_amount: str | None
    description: str | None
    
    def dict(self):
        """
        JSON serializable objects are required when Frappe returns them as
        responses.
        """
        return recursive_dataclass_to_dict(self)


def default_items_list() -> list[VA_DIAN_Item] | None:
    return []


@dataclass
class VA_DIAN_Document:
    """Information about a DIAN Document"""

    document_type: str
    document_id: str
    uuid: str
    issue_date: str
    issue_time: str
    sender_party_name: str
    sender_party_id: str
    sender_address: VA_DIAN_Address | None
    sender_email: str | None
    sender_telephone: str | None
    receiver_party_name: str | None
    receiver_party_id: str | None
    # items: list | None = field(default_factory=default_items_list, default=None)
    items: list[VA_DIAN_Item] | None = field(default=None)

    def dict(self):
        """
        JSON serializable objects are required when Frappe returns them as
        responses.
        """
        return recursive_dataclass_to_dict(self)

    def as_beauty_text(self):
        """
        Text that may be used for a nice representation of the extracted
        content.
        """
        return provide_nicely_formatted_dictionary(self.dict())

""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-04

--------------------------------------------------------------------------------

Data models.

---------------------------------------------------------------------------- """


from enum import StrEnum
from dataclasses import dataclass, field, asdict, is_dataclass


def recursive_dataclass_to_dict(data):
    if is_dataclass(data):
        return {key: recursive_dataclass_to_dict(value) for key, value in asdict(data).items()}
    elif isinstance(data, list):
        return [recursive_dataclass_to_dict(item) for item in data]
    elif isinstance(data, dict):
        return {key: recursive_dataclass_to_dict(value) for key, value in data.items()}
    else:
        return data


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
    numero_de_identificacion: str | None
    tipo_de_documento: str | None
    tipo_de_contribuyente: str | None
    primer_apellido: str | None
    segundo_apellido: str | None
    primer_nombre: str | None
    otros_nombres: str | None
    razon_social: str | None
    nombre_comercial: str | None
    direccion_principal: str | None
    correo_electronico: str | None
    telefono_1: str | None
    telefono_2: str | None
    codigo_postal: str | None
    ciudad_municipio: str | None
    departamento: str | None
    pais: str | None

    def dict(self):
        """
        JSON serializable objects are required when Frappe returns them as
        responses.
        """
        return recursive_dataclass_to_dict(self)


@dataclass
class VA_DIAN_Address:
    """Information about a DIAN Address"""

    street_name: str | None
    city_name: str | None
    postal_zone: str | None
    country: str | None

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
    uuid: str
    issue_date: str
    issue_time: str
    sender_party_name: str
    sender_party_id: str
    sender_address: VA_DIAN_Address | None
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

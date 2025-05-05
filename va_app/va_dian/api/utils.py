""" ----------------------------------------------------------------------------
Copyright (c) 2024-2025, VIDAL & ASTUDILLO Ltda and contributors
For license information, please see license.txt
By JMVA, VIDAL & ASTUDILLO Ltda
Version 2025-05-05

--------------------------------------------------------------------------------

Utils.

---------------------------------------------------------------------------- """


from dataclasses import (
    asdict, 
    is_dataclass,
)


def provide_nicely_formatted_dictionary(data: dict, indent=0) -> str:
    """
    Helper that provides a dictionary aimed to facilitate user selection of
    text.
    """

    result = ""
    for key, value in data.items():
        result += " " * indent + str(key) + ": "
        if isinstance(value, dict):
            result += "\n" + provide_nicely_formatted_dictionary(value, indent + 4)
        elif isinstance(value, list):
             result += "[" + ",".join(map(str, value)) + "]\n"
        else:
            result += str(value) + "\n"
    return result


def recursive_dataclass_to_dict(data):
    """
    Returns a dict from a dataclass, applying recursions to its elements in
    case those are dataclases themselves.
    """
    if is_dataclass(data):
        return {key: recursive_dataclass_to_dict(value) for key, value in asdict(data).items()}
    elif isinstance(data, list):
        return [recursive_dataclass_to_dict(item) for item in data]
    elif isinstance(data, dict):
        return {key: recursive_dataclass_to_dict(value) for key, value in data.items()}
    else:
        return data

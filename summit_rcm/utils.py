from re import sub
from typing import Any
from dbus_fast import Variant


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class InProgressException(Exception):
    """
    Exception Class for when the AT Interface is still executing a command
    """


def to_camel_case(string: str) -> str:
    """
    Return the given string formatted as camelCase.
    """
    string = sub(r"(_|-)+", " ", string).title().replace(" ", "")
    return "".join([string[0].lower(), string[1:]])


def camel_case_keys(original_dict: dict) -> dict:
    """
    Return a copy of the given dictionary with the keys formatted as camelCase.
    """
    new_dict = {}
    for key in original_dict.keys():
        new_dict[to_camel_case(key)] = original_dict[key]
    return new_dict


def variant_to_python(data: Any) -> Any:
    """Convert/unpack a Variant (or potentially variant) object to its value"""
    if isinstance(data, dict):
        return {k: variant_to_python(v) for k, v in data.items()}
    if isinstance(data, list):
        return [variant_to_python(item) for item in data]
    if isinstance(data, Variant):
        return variant_to_python(data.value)
    if isinstance(data, bytearray):
        return data.hex()
    return data

"""Module to hold various utility functions"""

import base64
import json
from re import sub
from typing import Any
from pathlib import Path
import os
import subprocess
import asyncio

try:
    from dbus_fast import Variant
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error


CMDLINE_BOOTSIDE_A = "ubi.block=0,1"
CMDLINE_BOOTSIDE_B = "ubi.block=0,4"


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


def get_current_side():
    """
    Return the current bootside
    """
    cmdline = Path("/proc/cmdline").read_text()
    if CMDLINE_BOOTSIDE_B in cmdline:
        return "b"
    elif CMDLINE_BOOTSIDE_A in cmdline:
        return "a"
    else:
        raise ValueError(
            "get_current_side: could not determine boot side from kernel cmdline"
        )


async def get_next_side() -> str:
    """
    Return the next bootside
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "fw_printenv",
            "-n",
            "bootside",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.decode("utf-8").strip())
        return stdout.decode("utf-8").strip().strip("'")
    except Exception as exception:
        raise ValueError(f"Unable to read next bootside: {str(exception)}")


def convert_dict_to_base64_string(json_dict: dict) -> str:
    """Convert the provided JSON object (dictionary) to a base64-encoded string"""
    if not isinstance(json_dict, dict):
        raise ValueError(f"Expected 'dict' not '{type(json_dict)}'")

    return base64.urlsafe_b64encode(json.dumps(json_dict).encode()).decode()


def convert_base64_string_to_dict(base64_string: str) -> dict:
    """Convert the provided base64-encoded string to a JSON object (dictionary)"""
    if not isinstance(base64_string, str):
        raise ValueError(f"Expected 'str' not '{type(base64_string)}'")

    return json.loads(base64.urlsafe_b64decode(base64_string.encode()).decode())

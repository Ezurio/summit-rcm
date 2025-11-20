#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold various utility functions"""

import base64
import json
from re import sub, match
import shlex
from typing import Any
import os
import subprocess
import asyncio

try:
    from dbus_fast import Variant
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error


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


def is_camel_case(string: str) -> bool:
    """
    Return whether the given string is formatted as camelCase.
    """
    return bool(match(r"^[a-z]+(?:[A-Z][a-z]+)*$", string))


def to_camel_case(string: str) -> str:
    """
    Return the given string formatted as camelCase.
    """
    if is_camel_case(string):
        return string
    string = sub(r"(_|-)+", " ", string).title().replace(" ", "")
    return "".join([string[0].lower(), string[1:]])


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


async def get_root_dev_type() -> str:
    """
    Return the current root device type
    """
    command = shlex.split("/bin/sh -c '. boot-rootfs.sh && echo $rootDevType'")
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    root_dev_type = stdout.decode("utf-8").strip()

    if root_dev_type not in ["SD", "MMC", "ubi"]:
        raise ValueError(
            f"get_root_dev_type: could not determine root device type: {root_dev_type}"
        )
    return root_dev_type


async def get_current_side() -> str:
    """
    Return the current bootside
    """
    command = shlex.split("/bin/sh -c '. boot-rootfs.sh && getSide && echo $bootside'")
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    bootside = stdout.decode("utf-8").strip()

    if bootside not in ["a", "b"]:
        raise ValueError(f"get_current_side: could not determine boot side: {bootside}")
    return bootside


async def get_next_side() -> str:
    """
    Return the next bootside
    """
    command = shlex.split("/bin/sh -c '. boot-rootfs.sh && nextSide'")
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    next_side = stdout.decode("utf-8").strip()

    if next_side not in ["a", "b"]:
        raise ValueError(f"get_next_side: could not determine next boot side: {next_side}")
    return next_side


async def get_base_hw_part_number() -> str:
    """
    Retrieve the base hardware part number of the currently-running device
    """
    command = shlex.split("/bin/sh -c '. boot-rootfs.sh && getBaseHwPartNumber'")
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    base_hw_part_number = stdout.decode("utf-8").strip()

    return base_hw_part_number


async def get_running_on_sd() -> bool:
    """Retrieve whether the system is running on the SD card"""
    try:
        return await get_root_dev_type() == "SD"
    except ValueError:
        return False


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


def frequency_to_channel(freq: int) -> int:
    """
    Convert an IEEE 802.11 frequency (in MHz) to a channel number.

    See ieee80211_freq_khz_to_channel() in the Linux kernel's net/wireless/util.c for more
    information.
    """
    if freq == 2484:
        return 14
    elif freq < 2484:
        return int((freq - 2407) / 5)
    elif freq >= 4910 and freq <= 4980:
        return int((freq - 4000) / 5)
    elif freq < 5925:
        return int((freq - 5000) / 5)
    elif freq == 5935:
        return 2
    elif freq <= 45000:
        return int((freq - 5950) / 5)
    elif freq >= 58320 and freq <= 70200:
        return int((freq - 56160) / 2160)
    else:
        return 0


async def convert_pkcs11_uri_to_pem(pkcs11_uri: str, output_path: str) -> None:
    """
    Convert a PKCS#11 URI to PEM format using the uri2pem.py script.

    Args:
        pkcs11_uri (str): The PKCS#11 URI to convert.
        output_path (str): The file path to save the PEM output.
    Raises:
        RuntimeError: If the conversion fails.
    """
    URI2PEM_SCRIPT_PATH = "/opt/pkcs11-provider/uri2pem.py"

    proc = await asyncio.create_subprocess_exec(
        "python3",
        URI2PEM_SCRIPT_PATH,
        "--out",
        output_path,
        pkcs11_uri,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to convert PKCS#11 URI to PEM: {stdout.decode('utf-8').strip()}"
        )


async def retrieve_certificate_from_pkcs11_uri(
    pkcs11_uri: str, output_path: str
) -> None:
    """
    Retrieve the certificate from a PKCS#11 URI using OpenSSL and save it to the specified output
    path.

    Args:
        pkcs11_uri (str): The PKCS#11 URI to retrieve the certificate from.
        output_path (str): The file path to save the retrieved certificate.
    Raises:
        RuntimeError: If the retrieval fails.
    """
    proc = await asyncio.create_subprocess_exec(
        "openssl",
        "x509",
        "-in",
        pkcs11_uri,
        "-out",
        output_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to retrieve certificate from PKCS#11 URI: {stderr.decode('utf-8').strip()}"
        )

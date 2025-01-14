#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle interfacing with logs
"""

import time
from datetime import datetime
import asyncio
import json
import os

try:
    from dbus_fast import Message, MessageType, Variant
    from summit_rcm.dbus_manager import DBusManager
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
from summit_rcm.utils import Singleton, variant_to_python
from summit_rcm.definition import (
    WPA_IFACE,
    WPA_OBJ,
    WIFI_DRIVER_DEBUG_PARAM,
    DBUS_PROP_IFACE,
    DriverLogLevelEnum,
    JournalctlLogTypesEnum,
    SupplicantLogLevelEnum,
)

JOURNALCTL_DAYS_SINCE_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
JOURNALCTL_LOG_ENTRY_FORMAT_STRING = "%Y-%m-%d %H:%M:%S.%f"


class LogsService(metaclass=Singleton):
    """Service to handle interfacing with logs"""

    @staticmethod
    def format_days_since_for_journalctl(days_since: int) -> str:
        """Format the given 'days_since' value for use with journalctl"""
        return datetime.fromtimestamp(time.time() - days_since * 86400).strftime(
            JOURNALCTL_DAYS_SINCE_FORMAT_STRING
        )

    @staticmethod
    async def get_journal_log_data(
        log_type: JournalctlLogTypesEnum, priority: int, days: int
    ) -> list:
        """Retrieve journal log data using the given parameters as a list"""
        if priority not in range(0, 8, 1):
            raise ValueError("Priority must be an int between 0-7")

        log_type = str(log_type.value).lower()
        if log_type == "networkmanager":
            log_type = "NetworkManager"
        elif log_type == "all":
            log_type = "All"
        elif log_type == "python":
            log_type = "summit-rcm"

        journalctl_args = [
            "journalctl",
            f"--priority={str(priority)}",
            "--output=json",
        ]
        if log_type != "All":
            journalctl_args.append(f"--identifier={str(log_type)}")
        if days > 0:
            journalctl_args.append(
                f"--since={LogsService.format_days_since_for_journalctl(days)}"
            )

        proc = await asyncio.create_subprocess_exec(
            *journalctl_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise JournalctlError(proc.returncode, stderr.decode("utf-8"))

        logs = []
        for line in str(stdout.decode("utf-8")).split("\n"):
            if line.strip() == "":
                # The last line is empty, so break if we see it
                break

            entry = json.loads(line)
            timestamp = str(entry.get("__REALTIME_TIMESTAMP", "Undefined"))
            logs.append(
                {
                    "time": datetime.fromtimestamp(float(timestamp) / 1000000).strftime(
                        JOURNALCTL_LOG_ENTRY_FORMAT_STRING
                    )
                    if timestamp != "Undefined"
                    else "Undefined",
                    "priority": str(entry.get("PRIORITY", 7)),
                    "identifier": entry.get("SYSLOG_IDENTIFIER", "Undefined"),
                    "message": entry.get("MESSAGE", "Undefined"),
                }
            )
        return logs

    @staticmethod
    async def get_supplicant_debug_level() -> SupplicantLogLevelEnum:
        """Retrieve the supplication debug level ('DebugLevel' property)"""

        bus = await DBusManager().get_bus()
        reply = await bus.call(
            Message(
                destination=WPA_IFACE,
                path=WPA_OBJ,
                interface=DBUS_PROP_IFACE,
                member="Get",
                signature="ss",
                body=[WPA_IFACE, "DebugLevel"],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        return SupplicantLogLevelEnum(str(variant_to_python(reply.body[0])))

    @staticmethod
    async def set_supplicant_debug_level(supp_level: SupplicantLogLevelEnum):
        """Configure the supplication debug level ('DebugLevel' property)"""

        bus = await DBusManager().get_bus()
        reply = await bus.call(
            Message(
                destination=WPA_IFACE,
                path=WPA_OBJ,
                interface=DBUS_PROP_IFACE,
                member="Set",
                signature="ssv",
                body=[WPA_IFACE, "DebugLevel", Variant("s", supp_level.value)],
            )
        )

        if reply.message_type == MessageType.ERROR:
            raise Exception(
                f"Error setting supplicant 'DebugLevel' to {supp_level.value}"
            )

    @staticmethod
    def get_wifi_driver_debug_level() -> DriverLogLevelEnum:
        """Retrieve the Wi-Fi driver's debug level"""

        with open(WIFI_DRIVER_DEBUG_PARAM, "r") as driver_debug_file:
            if driver_debug_file.mode == "r":
                return DriverLogLevelEnum(driver_debug_file.read(1))

    @staticmethod
    def set_wifi_driver_debug_level(drv_level: DriverLogLevelEnum):
        """Configure the Wi-Fi driver's debug level"""

        with open(WIFI_DRIVER_DEBUG_PARAM, "w") as driver_debug_file:
            if driver_debug_file.mode == "w":
                driver_debug_file.write(str(drv_level.value))


class JournalctlError(Exception):
    """Custom error class for when an error occurs while running journalctl"""

    def __init__(self, return_code: int, *args: object) -> None:
        super().__init__(*args)
        self.return_code = return_code

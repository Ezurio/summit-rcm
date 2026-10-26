#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to interact with the system date/time settings.
"""

from syslog import syslog, LOG_ERR
import time
from typing import Tuple, List
from datetime import datetime, timezone
import os

try:
    from dbus_fast import Message, MessageType
    from summit_rcm.dbus_manager import DBusManager
except ImportError as error:
    # Ignore the error if the dbus_fast module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error

    Message = None
    MessageType = None

from summit_rcm.definition import (
    DBUS_PROP_IFACE,
    TIMEDATE1_BUS_NAME,
    TIMEDATE1_MAIN_OBJ,
    SUMMIT_RCM_TIME_FORMAT,
)
from summit_rcm.utils import Singleton

LOCALTIME = "/etc/localtime"
ZONEINFO = "/usr/share/zoneinfo/"
ETC_TIMEZONE = "/etc/timezone"


class DateTimeService(metaclass=Singleton):
    """Service to interact with the system date/time setttings."""

    def __init__(self):
        self._zones: List[str] = []
        self._zones_populated: bool = False

    @property
    def zones(self) -> List[str]:
        """
        List of available time zones
        """
        return self._zones

    async def get_local_zone(self) -> str:
        """
        Current local time zone
        """
        try:
            bus = await DBusManager().get_bus()
            reply = await bus.call(
                Message(
                    destination=TIMEDATE1_BUS_NAME,
                    path=TIMEDATE1_MAIN_OBJ,
                    interface=DBUS_PROP_IFACE,
                    member="Get",
                    signature="ss",
                    body=[TIMEDATE1_BUS_NAME, "Timezone"],
                )
            )
            if reply.message_type == MessageType.ERROR:
                raise RuntimeError(reply.body[0])

            zone_name = reply.body[0].value
            if isinstance(zone_name, str) and zone_name:
                return zone_name
            raise ValueError("Invalid timedated timezone property")
        except Exception as exception:
            syslog(LOG_ERR, f"Could not read timedated timezone: {str(exception)}")

        # Fallback to reading /etc/localtime symlink if timedated fails
        try:
            localtime_target = os.readlink(LOCALTIME)
            if not os.path.isabs(localtime_target):
                localtime_target = os.path.join(
                    os.path.dirname(LOCALTIME), localtime_target
                )
            localtime_target = os.path.abspath(localtime_target)
            zoneinfo_path = os.path.abspath(ZONEINFO)
            if os.path.commonpath((zoneinfo_path, localtime_target)) == zoneinfo_path:
                zone = os.path.relpath(localtime_target, zoneinfo_path)
                if zone.startswith("posix/"):
                    zone = zone[len("posix/") :]
                return zone
        except (OSError, ValueError):
            pass

        # Fallback to reading /etc/timezone if /etc/localtime symlink fails
        try:
            with open(ETC_TIMEZONE, "r") as etc_timezone_file:
                return etc_timezone_file.readline().strip()
        except Exception as exception:
            syslog(LOG_ERR, f"Get local time zone failure: {str(exception)}")
            return "Unable to determine timezone"

    async def populate_time_zone_list(self):
        """
        Populate the list of available time zones from systemd-timedated.
        """
        if self._zones_populated:
            return
        self._zones_populated = True

        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=TIMEDATE1_BUS_NAME,
                    path=TIMEDATE1_MAIN_OBJ,
                    interface=TIMEDATE1_BUS_NAME,
                    member="ListTimezones",
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            self._zones = reply.body[0]
        except Exception as exception:
            syslog(LOG_ERR, f"Could not populate time zone list: {str(exception)}")
            self._zones = []
            self._zones_populated = False

    @staticmethod
    async def set_time_zone(new_zone: str):
        """
        Call the SetTimezone() method passing the provided time zone and set the 'interactive'
        parameter to False.

        See below for more info:
        https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
        """
        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=TIMEDATE1_BUS_NAME,
                    path=TIMEDATE1_MAIN_OBJ,
                    interface=TIMEDATE1_BUS_NAME,
                    member="SetTimezone",
                    signature="sb",
                    body=[new_zone, False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to set timezone - {str(exception)}")

        # Re-evaluate the timezone - this is necessary as the Summit RCM Python process itself
        # doesn't automatically pick up on the timezone change.
        time.tzset()

    @staticmethod
    def check_current_date_and_time() -> Tuple[bool, str]:
        """
        Retrieve the current date/time adjusted for the current time zone.

        The return value is a tuple containing a boolean indicating success/failure and a string
        (the current date and time for success, otherwise an error message).
        """
        try:
            # Re-evaluate the timezone - this is necessary as the Summit RCM Python process itself
            # doesn't automatically pick up on the timezone change.
            time.tzset()

            return (
                True,
                datetime.now(timezone.utc)
                .astimezone()
                .strftime(SUMMIT_RCM_TIME_FORMAT),
            )
        except Exception as exception:
            syslog(LOG_ERR, f"Get current date and time failure: {str(exception)}")
            return (False, f"Get current date and time failure: {str(exception)}")

    @staticmethod
    async def set_time_manual(dt: str):
        """
        Call the SetTime() method passing the provided timestamp (in usec_utc), set the 'relative'
        parameter to False, and set the 'interactive' parameter to False.

        See below for more info:
        https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
        """
        try:
            dt_int = int(dt)
        except ValueError:
            # Could not convert the provided timestamp to an integer - try to parse it as a
            # datetime string.
            try:
                dt_int = int(
                    datetime.strptime(dt, SUMMIT_RCM_TIME_FORMAT)
                    .replace(tzinfo=timezone.utc)
                    .timestamp()
                    * 1_000_000
                )
            except Exception as exception:
                raise ValueError("Unable to parse datetime") from exception

        bus = await DBusManager().get_bus()

        reply = await bus.call(
            Message(
                destination=TIMEDATE1_BUS_NAME,
                path=TIMEDATE1_MAIN_OBJ,
                interface=TIMEDATE1_BUS_NAME,
                member="SetTime",
                signature="xbb",
                body=[dt_int, False, False],
            )
        )

        if reply.message_type == MessageType.ERROR:
            error_name = reply.error_name or "Unknown D-Bus error"
            error_message = str(reply.body[0]) if reply.body else "SetTime failed"
            if error_name == "org.freedesktop.DBus.Error.InvalidArgs":
                raise ValueError(error_message)
            raise RuntimeError(f"{error_name}: {error_message}")

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
from summit_rcm.definition import (
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

    @property
    def local_zone(self) -> str:
        """
        Current local time zone
        """
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
            except Exception:
                raise Exception("Unable to parse datetime")

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
            raise Exception("Error calling SetTime")

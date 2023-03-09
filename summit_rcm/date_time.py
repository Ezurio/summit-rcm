from syslog import syslog, LOG_ERR
import time
from typing import Tuple, List
from dbus_fast import Message, MessageType
import falcon
from .definition import (
    TIMEDATE1_BUS_NAME,
    TIMEDATE1_MAIN_OBJ,
    SUMMIT_RCM_ERRORS,
    SUMMIT_RCM_TIME_FORMAT,
)

from datetime import datetime, timezone
from .dbus_manager import DBusManager

LOCALTIME = "/etc/localtime"
ZONEINFO = "/usr/share/zoneinfo/"
ETC_TIMEZONE = "/etc/timezone"


class DateTimeSetting:
    def __init__(self):
        self._zones: List[str] = []

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
        except Exception as e:
            syslog(LOG_ERR, f"Get local time zone failure: {str(e)}")
            return "Unable to determine timezone"

    async def set_time_zone(self, new_zone: str):
        # Call the SetTimezone() method passing the provided time zone and set the
        # 'interactive' parameter to False.
        # See below for more info:
        # https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
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
        except Exception as e:
            syslog(LOG_ERR, f"Unable to set timezone - {str(e)}")

        # Re-evaluate the timezone - this is necessary as the Summit RCM Python process itself
        # doesn't automatically pick up on the timezone change.
        time.tzset()

    async def populate_time_zone_list(self):
        """
        Populate the list of available time zones from systemd-timedated.
        """
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
        except Exception as e:
            syslog(LOG_ERR, f"Could not populate time zone list: {str(e)}")
            self._zones = []

    def check_current_date_and_time(self) -> Tuple[bool, str]:
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
        except Exception as e:
            syslog(LOG_ERR, f"Get current date and time failure: {str(e)}")
            return (False, f"Get current date and time failure: {str(e)}")

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        result["zones"] = self.zones
        result["zone"] = self.local_zone

        success, msg = self.check_current_date_and_time()
        if success:
            result["method"] = "auto"
            result["time"] = msg.strip()
        else:
            result["method"] = "manual"
            result["time"] = ""

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        post_data = await req.get_media()
        zone = post_data.get("zone", "")
        method = post_data.get("method", "")
        dt = post_data.get("datetime", "")

        # Setting the timezone was initially supported when 'zone' was not an empty string so
        # re-create that here.
        if zone != "":
            try:
                await self.set_time_zone(zone)
            except Exception as e:
                syslog(LOG_ERR, f"Could not set timezone: {str(e)}")
                result["InfoMsg"] = f"Could not set timezone: {str(e)}"
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                resp.media = result
                return
        # Setting the time was initially supported when 'method' is set to 'manual' so re-create
        # that here.
        elif method == "manual" and dt != "":
            try:
                # Call the SetTime() method passing the provided timestamp (in usec_utc), set the
                # 'relative' parameter to False, and set the 'interactive' parameter to False.
                # See below for more info:
                # https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
                bus = await DBusManager().get_bus()

                reply = await bus.call(
                    Message(
                        destination=TIMEDATE1_BUS_NAME,
                        path=TIMEDATE1_MAIN_OBJ,
                        interface=TIMEDATE1_BUS_NAME,
                        member="SetTime",
                        signature="xbb",
                        body=[int(dt), False, False],
                    )
                )

                if reply.message_type == MessageType.ERROR:
                    raise Exception(reply.body[0])
            except Exception as e:
                syslog(LOG_ERR, f"Could not set datetime: {str(e)}")
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                result["InfoMsg"] = "Could not set datetime"
                resp.media = result
                return

        # Unless we hit an error, the previous logic would return the current date and time (and
        # timezone), so re-create that here.
        success, msg = self.check_current_date_and_time()
        if success:
            result["time"] = msg
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = self.local_zone
        else:
            result["InfoMsg"] = msg
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        resp.media = result

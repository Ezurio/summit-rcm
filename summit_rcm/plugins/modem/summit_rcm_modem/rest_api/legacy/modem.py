from dbus_fast import Message, MessageType, Variant
import falcon
import os
from summit_rcm.systemd_unit import SystemdUnit
from summit_rcm.dbus_manager import DBusManager
from syslog import syslog
from summit_rcm.definition import (
    SUMMIT_RCM_ERRORS,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
    MODEM_FIRMWARE_UPDATE_FILE,
    MODEM_FIRMWARE_UPDATE_DST_DIR,
    MODEM_FIRMWARE_UPDATE_SRC_DIR,
    MODEM_ENABLE_FILE,
    MODEM_CONTROL_SERVICE_FILE,
)
from pathlib import Path


def dbus_fast_to_python(data):
    """
    Convert dbus_fast data types to python native data types
    """
    if isinstance(data, Variant):
        data = data.value
    elif isinstance(data, list):
        data = [dbus_fast_to_python(value) for value in data]
    elif isinstance(data, dict):
        new_data = dict()
        for key in data.keys():
            new_key = dbus_fast_to_python(key)
            new_data[str(new_key)] = dbus_fast_to_python(data[key])
        data = new_data
    else:
        data = data
    return data


class Modem(object):
    async def get_modem_obj_path(self) -> str:
        """
        Retrieve the D-Bus object path to the modem managed by ModemManager. If no modem is found,
        an empty string is returned.
        """
        bus = await DBusManager().get_bus()

        try:
            # Call the 'GetManagedObjects' D-Bus function which is available because
            # org.freedesktop.ModemManager1 implements the org.freedesktop.DBus.ObjectManager
            # interface.
            # See here for more details:
            # https://dbus.freedesktop.org/doc/dbus-specification.html#standard-interfaces-objectmanager
            reply = await bus.call(
                Message(
                    destination="org.freedesktop.ModemManager1",
                    path="/org/freedesktop/ModemManager1",
                    interface="org.freedesktop.DBus.ObjectManager",
                    member="GetManagedObjects",
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            for key in reply.body[0].keys():
                # For now, we only support the one modem, so just return the first one we find
                return key
        except Exception as e:
            syslog(f"Could not get modem object path - {str(e)}")
        return ""


class PositioningSwitch(Modem):

    _source = 0

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS"),
            "positioning": PositioningSwitch._source,
        }
        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")}

        try:
            post_data = await req.get_media()
            source = post_data.get("positioning", 0)
            if (PositioningSwitch._source != source) and (
                not source or not PositioningSwitch._source
            ):
                bus = await DBusManager().get_bus()

                # Call the 'Setup' D-Bus function
                # See here for more details:
                # https://www.freedesktop.org/software/ModemManager/doc/latest/ModemManager/gdbus-org.freedesktop.ModemManager1.Modem.Location.html
                reply = await bus.call(
                    Message(
                        destination="org.freedesktop.ModemManager1",
                        path=await self.get_modem_obj_path(),
                        interface="org.freedesktop.ModemManager1.Modem.Location",
                        member="Setup",
                        signature="ub",
                        body=[source, False],
                    )
                )

                if reply.message_type == MessageType.ERROR:
                    raise Exception(reply.body[0])

                PositioningSwitch._source = source
                result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        except Exception as e:
            syslog(f"Enable/disable positioning failed: {str(e)}")

        result["positioning"] = PositioningSwitch._source
        resp.media = result


class Positioning(Modem):
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")}

        try:
            bus = await DBusManager().get_bus()

            # Call the 'GetLocation' D-Bus function
            # See here for more details:
            # https://www.freedesktop.org/software/ModemManager/doc/latest/ModemManager/gdbus-org.freedesktop.ModemManager1.Modem.Location.html
            reply = await bus.call(
                Message(
                    destination="org.freedesktop.ModemManager1",
                    path=await self.get_modem_obj_path(),
                    interface="org.freedesktop.ModemManager1.Modem.Location",
                    member="GetLocation",
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            result["positioning"] = dbus_fast_to_python(reply.body[0])
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        except Exception as e:
            syslog(f"Get positioning data failed: {str(e)}")

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")}

        post_data = await req.get_media()
        token = post_data.get("token", 0)
        if not token:
            resp.media = result
            return

        try:
            bus = await DBusManager().get_bus()

            # Call the 'InjectAssistanceData' D-Bus function
            # See here for more details:
            # https://www.freedesktop.org/software/ModemManager/doc/latest/ModemManager/gdbus-org.freedesktop.ModemManager1.Modem.Location.html
            reply = await bus.call(
                Message(
                    destination="org.freedesktop.ModemManager1",
                    path=await self.get_modem_obj_path(),
                    interface="org.freedesktop.ModemManager1.Modem.Location",
                    member="InjectAssistanceData",
                    signature="ay",
                    body=[bytearray(token.encode("utf-8"))],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        except Exception as e:
            syslog(f"Set token failed: {str(e)}")

        return result


class ModemFirmwareUpdate(object):
    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_FAIL"),
            "InfoMsg": "",
            "Status": "not-updating",  # options are not-updating, in-progress, queued
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] = "Modem firmware update already in progress"
            result["Status"] = "in-progress"
            resp.media = result
            return

        if os.path.exists(MODEM_FIRMWARE_UPDATE_FILE):
            result["InfoMsg"] = "Modem firmware update already queued for next boot"
            result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
            result["Status"] = "queued"
            resp.media = result
            return

        if not os.path.isdir(MODEM_FIRMWARE_UPDATE_SRC_DIR):
            result["InfoMsg"] = "No modem firmware update file available"
            resp.media = result
            return

        flist = []
        for path in os.listdir(MODEM_FIRMWARE_UPDATE_SRC_DIR):
            if os.path.isfile(os.path.join(MODEM_FIRMWARE_UPDATE_SRC_DIR, path)):
                flist.append(path)

        if len(flist) == 0:
            result["InfoMsg"] = (
                "No firmware files found in %s" % MODEM_FIRMWARE_UPDATE_SRC_DIR
            )
            resp.media = result
            return

        try:
            os.makedirs(MODEM_FIRMWARE_UPDATE_DST_DIR, mode=0o755, exist_ok=True)
        except Exception as e:
            syslog("Unable to create directory: %s" % e)
            result["InfoMsg"] = (
                "Unable to create directory for firmware update file: %s" % e
            )
            resp.media = result
            return

        if (len(flist)) > 1:
            result["InfoMsg"] = (
                "Multiple firmware files located in %s - "
                % MODEM_FIRMWARE_UPDATE_SRC_DIR
            )

        try:
            os.symlink(
                os.path.join(MODEM_FIRMWARE_UPDATE_SRC_DIR, flist[0]),
                MODEM_FIRMWARE_UPDATE_FILE,
            )
        except Exception as e:
            syslog("Unable to create symlink: %s" % e)
            result["InfoMsg"] = (
                "Unable to create symlink for firmware update file: %s" % e
            )
            resp.media = result
            return

        syslog(
            "Modem firmware update file queued for installation.  File: %s"
            % os.path.join(MODEM_FIRMWARE_UPDATE_SRC_DIR, flist[0])
        )
        result["InfoMsg"] += "Modem Firmware Update queued for next boot"
        result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        result["Status"] = "queued"

        resp.media = result

    async def do_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "No modem firmware update in progress",
            "Status": "not-updating",  # options are not-updating, in-progress, queued
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] = "Modem firmware update in progress"
            result["Status"] = "in-progress"
        elif os.path.exists(MODEM_FIRMWARE_UPDATE_FILE):
            result["InfoMsg"] = "Modem firmware update queued for next boot"
            result["Status"] = "queued"

        resp.media = result


class ModemEnable(SystemdUnit):
    def __init__(self) -> None:
        super().__init__(MODEM_CONTROL_SERVICE_FILE)

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")}

        enable = False
        if os.path.exists(MODEM_ENABLE_FILE):
            enable = True

        result["modem_enabled"] = True if enable else False
        result["InfoMsg"] = "Modem is %s" % ("enabled" if enable else "disabled")
        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {}
        enable_test = -1
        result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_FAIL")
        try:
            enable = req.params.get("enable")
            enable = enable.lower()
            if enable in ("y", "yes", "t", "true", "on", "1"):
                enable_test = 1
            elif enable in ("n", "no", "f", "false", "off", "0"):
                enable_test = 0
            if enable_test < 0:
                raise ValueError("illegal value passed in")
        except Exception:
            result["infoMsg"] = (
                "unable to set modem enable. Supplied enable parameter '%s' invalid."
                % req.params.get("enable")
            )

            resp.media = result
            return

        enable = False
        if os.path.exists(MODEM_ENABLE_FILE):
            enable = True

        result["SDCERR"] = SUMMIT_RCM_ERRORS.get("SDCERR_SUCCESS")
        if enable and enable_test == 1:
            result["InfoMsg"] = "modem already enabled. No change"
            result["modem_enabled"] = True
        elif (not enable) and enable_test == 0:
            result["InfoMsg"] = "modem already disabled. No change"
            result["modem_enabled"] = False
        else:

            try:
                if enable_test == 1:
                    # enable on device
                    Path(MODEM_ENABLE_FILE).touch()

                    if not self.activate():
                        result["InfoMsg"] = "Unable to enable modem"
                        resp.media = result
                        return
                else:
                    if not self.deactivate():
                        result["InfoMsg"] = "Unable to disable modem"
                        resp.media = result
                        return
                    # disable on device
                    os.remove(MODEM_ENABLE_FILE)
            except Exception as e:
                result["InfoMsg"] = "{}".format(e)
                resp.media = result
                return

            result["modem_enabled"] = enable_test == 1
            result["InfoMsg"] = "Modem is %s" % (
                "enabled" if enable_test == 1 else "disabled"
            )
        resp.media = result

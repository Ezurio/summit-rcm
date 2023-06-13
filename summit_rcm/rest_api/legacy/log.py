import json
import os
from syslog import LOG_ERR, syslog
from dbus_fast import Message, MessageType
import falcon
import time
from summit_rcm.dbus_manager import DBusManager
from datetime import datetime
from summit_rcm.systemd_unit import SystemdUnit
from summit_rcm.settings import SystemSettingsManage
from subprocess import run
from summit_rcm.definition import (
    LOG_FORWARDING_ENABLED_FLAG_FILE,
    SUMMIT_RCM_ERRORS,
    WPA_IFACE,
    WPA_OBJ,
    WIFI_DRIVER_DEBUG_PARAM,
    DBUS_PROP_IFACE,
    SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE,
)


class LogData:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            priority = int(req.params.get("priority", 7))
        except Exception as e:
            syslog(
                LOG_ERR, f"Error parsing 'priority' parameter as an integer: {str(e)}"
            )
            resp.media = {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
            return
        if priority not in range(0, 8, 1):
            resp.media = {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
            return
        # use .lower() to ensure incoming type has comparable case
        typ = req.params.get("type", "All").lower()
        # TODO - documentation says 'python' is lower case while others are upper/mixed case.
        if typ == "networkmanager":
            typ = "NetworkManager"
        elif typ == "all":
            typ = "All"
        elif typ == "python":
            typ = "summit-rcm"
        types = {
            "kernel",
            "NetworkManager",
            "summit-rcm",
            "adaptive_ww",
            "All",
        }
        if typ not in types:
            resp.media = {
                "SDCERR": 1,
                "InfoMsg": f"supplied type parameter must be one of {str(types)}",
            }
            return
        try:
            days = int(req.params.get("days", 1))
        except Exception as e:
            syslog(LOG_ERR, f"Error parsing 'days' parameter as an integer: {str(e)}")
            resp.media = {"SDCERR": 1, "InfoMsg": "days must be an int"}
            return

        try:
            journalctl_args = [
                "journalctl",
                f"--priority={str(priority)}",
                "--output=json",
            ]
            if typ != "All":
                journalctl_args.append(f"--identifier={str(typ)}")
            if days > 0:
                journalctl_args.append(
                    f"--since={datetime.fromtimestamp(time.time() - days * 86400).strftime('%Y-%m-%d %H:%M:%S')}"
                )

            proc = run(
                journalctl_args,
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if proc.returncode == 0:
                logs = []
                for line in str(proc.stdout.decode("utf-8")).split("\n"):
                    if line.strip() == "":
                        # The last line is empty, so break if we see it
                        break
                    entry = json.loads(line)
                    log = {}
                    timestamp = str(entry.get("__REALTIME_TIMESTAMP", "Undefined"))
                    log["time"] = (
                        datetime.fromtimestamp(float(timestamp) / 1000000).strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )
                        if timestamp != "Undefined"
                        else "Undefined"
                    )
                    log["priority"] = str(entry.get("PRIORITY", 7))
                    log["identifier"] = entry.get("SYSLOG_IDENTIFIER", "Undefined")
                    log["message"] = entry.get("MESSAGE", "Undefined")
                    logs.append(log)
                result["InfoMsg"] = f"type: {typ}; days: {days}; Priority: {priority}"
                result["count"] = len(logs)
                result["log"] = logs
                resp.media = result
            else:
                syslog(
                    LOG_ERR,
                    f"journalctl error - returncode: {str(proc.returncode)}, stderr: {str(proc.stderr.decode('utf-8'))}",
                )
                resp.media = {"SDCERR": 1, "InfoMsg": "Could not read journal logs"}

        except Exception as e:
            syslog(LOG_ERR, f"Could not read journal logs: {str(e)}")
            resp.media = {"SDCERR": 1, "InfoMsg": "Could not read journal logs"}


class LogForwarding(SystemdUnit):
    def __init__(self) -> None:
        super().__init__(SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE)

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not retrieve log forwarding state",
            "state": "unknown",
        }

        try:
            result["state"] = await self.get_active_state()
            if result["state"] != "unknown":
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = ""
        except Exception as e:
            syslog(LOG_ERR, f"Could not retrieve log forwarding state: {str(e)}")

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not set log forwarding state",
        }

        try:
            valid_states = ["active", "inactive"]

            post_data = await req.get_media()
            requested_state = post_data.get("state", None)
            if not requested_state:
                result["InfoMsg"] = f"Invalid state; valid states: {valid_states}"
                resp.media = result
                return
            if requested_state not in valid_states:
                result[
                    "InfoMsg"
                ] = f"Invalid state: {requested_state}; valid states: {valid_states}"
                resp.media = result
                return

            # Read the current 'ActiveState' of the log forwarding service
            current_state = await self.get_active_state()

            if requested_state == "active":
                # Create the 'flag file' which systemd uses to determine if it should start the
                # systemd-journal-gatewayd.socket unit.
                with open(LOG_FORWARDING_ENABLED_FLAG_FILE, "w"):
                    pass

                if current_state == "active":
                    # Service already active
                    result["InfoMsg"] = "Log forwarding already active"
                    result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                else:
                    # Activate service
                    if await self.activate():
                        result["InfoMsg"] = "Log forwarding activated"
                        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            elif requested_state == "inactive":
                # Remove the 'flag file' which systemd uses to determine if it should start the
                # systemd-journal-gatewayd.socket unit.
                try:
                    os.remove(LOG_FORWARDING_ENABLED_FLAG_FILE)
                except OSError:
                    # Handle the case where the file isn't already present
                    pass

                if current_state == "inactive":
                    # Service is already inactive
                    result["InfoMsg"] = "Log forwarding already inactive"
                    result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                else:
                    # Deactivate service
                    if await self.deactivate():
                        result["InfoMsg"] = "Log forwarding deactivated"
                        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            syslog(LOG_ERR, f"Could not set log forwarding state: {str(e)}")
            result = {
                "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set log forwarding state",
            }

        resp.media = result


class LogSetting:
    async def on_post(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": ""}
        post_data = await req.get_media()

        if "suppDebugLevel" not in post_data:
            result["InfoMsg"] = "suppDebugLevel missing from JSON data"
            resp.media = result
            return
        if "driverDebugLevel" not in post_data:
            result["InfoMsg"] = "driverDebugLevel missing from JSON data"
            resp.media = result
            return

        levels = {"none", "error", "warning", "info", "debug", "msgdump", "excessive"}
        supp_level = post_data.get("suppDebugLevel").lower()
        if supp_level not in levels:
            result["InfoMsg"] = f"suppDebugLevel must be one of {levels}"
            resp.media = result
            return

        try:
            bus = await DBusManager().get_bus()

            reply = await bus.call(
                Message(
                    destination=WPA_IFACE,
                    path=WPA_OBJ,
                    interface=DBUS_PROP_IFACE,
                    member="Set",
                    signature="sss",
                    body=[WPA_IFACE, "DebugLevel", supp_level],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])
            # bus = DBusManager().get_bus()
            # proxy = bus.get_proxy_object(
            #     WPA_IFACE, WPA_OBJ, bus.introspect_sync(WPA_IFACE, WPA_OBJ)
            # )
            # wpas = proxy.get_interface(DBUS_PROP_IFACE)
            # wpas.call_set_sync(WPA_IFACE, "DebugLevel", supp_level)
        except Exception as e:
            syslog(LOG_ERR, f"unable to set supplicant debug level: {str(e)}")
            result["InfoMsg"] = "unable to set supplicant debug level"
            resp.media = result
            return

        drv_level = post_data.get("driverDebugLevel")
        try:
            drv_level = int(drv_level)
        except Exception:
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            resp.media = result
            return

        if not (drv_level == 0 or drv_level == 1):
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            resp.media = result
            return

        try:
            driver_debug_file = open(WIFI_DRIVER_DEBUG_PARAM, "w")
            if driver_debug_file.mode == "w":
                driver_debug_file.write(str(drv_level))
        except Exception as e:
            syslog(LOG_ERR, f"unable to set driver debug level: {str(e)}")
            result["InfoMsg"] = "unable to set driver debug level"
            resp.media = result
            return

        result["SDCERR"] = 0
        result[
            "InfoMsg"
        ] = f"Supplicant debug level = {supp_level}; Driver debug level = {drv_level}"

        resp.media = result

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            # bus = DBusManager().get_bus()
            # proxy = bus.get_proxy_object(
            #     WPA_IFACE, WPA_OBJ, bus.introspect_sync(WPA_IFACE, WPA_OBJ)
            # )
            # wpas = proxy.get_interface(DBUS_PROP_IFACE)
            # debug_level = wpas.call_get_sync(WPA_IFACE, "DebugLevel")
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

            result["suppDebugLevel"] = reply.body[0]
        except Exception as e:
            syslog(LOG_ERR, f"Unable to determine supplicant debug level: {str(e)}")
            result["Errormsg"] = "Unable to determine supplicant debug level"
            result["SDCERR"] = 1

        try:
            driver_debug_file = open(WIFI_DRIVER_DEBUG_PARAM, "r")
            if driver_debug_file.mode == "r":
                contents = driver_debug_file.read(1)
                result["driverDebugLevel"] = contents
        except Exception as e:
            syslog(LOG_ERR, f"Unable to determine driver debug level: {str(e)}")
            if result.get("SDCERR") == 0:
                result["Errormsg"] = "Unable to determine driver debug level"
            else:
                result[
                    "Errormsg"
                ] = "Unable to determine supplicant nor driver debug level"
            result["SDCERR"] = 1

        resp.media = result

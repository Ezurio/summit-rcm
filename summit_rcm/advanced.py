from dbus_fast import Message, MessageType
import falcon
import os
from syslog import syslog, LOG_ERR
from subprocess import run, call, TimeoutExpired, CalledProcessError
from .definition import (
    SUMMIT_RCM_ERRORS,
    LOGIND_BUS_NAME,
    LOGIND_MAIN_OBJ,
    LOGIND_MAIN_IFACE,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
)
from .settings import SystemSettingsManage
from .dbus_manager import DBusManager


class PowerOff:
    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Poweroff cannot be initiated",
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            resp.media = result
            return

        try:
            bus = await DBusManager().get_bus()

            # Call PowerOff() (non-interactive)
            reply = await bus.call(
                Message(
                    destination=LOGIND_BUS_NAME,
                    path=LOGIND_MAIN_OBJ,
                    interface=LOGIND_MAIN_IFACE,
                    member="PowerOff",
                    signature="b",
                    body=[False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = "Poweroff initiated"
        except Exception as e:
            syslog(LOG_ERR, f"Poweroff cannot be initiated: {str(e)}")

        resp.media = result


class Suspend:
    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Suspend cannot be initiated",
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            resp.media = result
            return

        try:
            bus = await DBusManager().get_bus()

            # Call Suspend() (non-interactive)
            reply = await bus.call(
                Message(
                    destination=LOGIND_BUS_NAME,
                    path=LOGIND_MAIN_OBJ,
                    interface=LOGIND_MAIN_IFACE,
                    member="Suspend",
                    signature="b",
                    body=[False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = "Suspend initiated"

        except Exception as e:
            syslog(LOG_ERR, f"Suspend cannot be initiated: {str(e)}")

        resp.media = result


class Reboot:
    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Reboot cannot be initiated",
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            resp.media = result
            return

        try:
            bus = await DBusManager().get_bus()

            # Call Reboot() (non-interactive)
            reply = await bus.call(
                Message(
                    destination=LOGIND_BUS_NAME,
                    path=LOGIND_MAIN_OBJ,
                    interface=LOGIND_MAIN_IFACE,
                    member="Reboot",
                    signature="b",
                    body=[False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = "Reboot initiated"
        except Exception as e:
            syslog(LOG_ERR, f"Reboot cannot be initiated: {str(e)}")

        resp.media = result


class FactoryReset:
    FACTORY_RESET_SCRIPT = "/usr/sbin/do_factory_reset.sh"

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "FactoryReset cannot be initiated",
        }

        if not os.path.exists(self.FACTORY_RESET_SCRIPT):
            result["InfoMsg"] += " - not available on non-encrypted file system images"
            resp.media = result
            return

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            resp.media = result
            return

        syslog("Factory Reset requested")
        try:
            returncode = call([self.FACTORY_RESET_SCRIPT, "reset"])
        except BaseException:
            returncode = -1
        result["SDCERR"] = returncode
        if returncode == 0:
            result["InfoMsg"] = "Reboot required"
        else:
            result["InfoMsg"] = "Error running factory reset"
            syslog("FactoryReset's returned % d" % returncode)

        resp.media = result


class Fips:

    FIPS_SCRIPT = "/usr/bin/fips-set"

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Reboot required",
        }

        setOptions = ["unset", "fips", "fips_wifi"]

        post_data = await req.get_media()
        fips = post_data.get("fips", None)
        if fips not in setOptions:
            result["InfoMsg"] = f"Invalid option: {fips}; valid options: {setOptions}"
            resp.media = result
            return

        try:
            run(
                [Fips.FIPS_SCRIPT, fips],
                check=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        except CalledProcessError as e:
            syslog("FIPS set error: %d" % e.returncode)
            result["InfoMsg"] = "FIPS SET error"

        except FileNotFoundError:
            result["InfoMsg"] = "Not a FIPS image"

        except TimeoutExpired as e:
            syslog("FIPS SET timeout: %s" % e)
            result["InfoMsg"] = "FIPS SET timeout"

        except Exception as e:
            syslog("FIPS set exception: %s" % e)
            result["InfoMsg"] = "FIPS SET exception: {}".format(e)

        try:
            from .stunnel.stunnel import Stunnel

            if fips == "fips" or fips == "fips_wifi":
                Stunnel.configure_fips(enabled=True)
            elif fips == "unset":
                Stunnel.configure_fips(enabled=False)
        except ImportError:
            # stunnel module not loaded
            pass
        except Exception as e:
            syslog("FIPS stunnel set exception: %s" % e)
            result["InfoMsg"] = "FIPS stunnel SET exception: {}".format(e)

        resp.media = result

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
            "status": "unset",
        }

        try:
            p = run(
                [Fips.FIPS_SCRIPT, "status"],
                capture_output=True,
                check=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            result["status"] = p.stdout.decode("utf-8").strip()
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        except CalledProcessError as e:
            syslog("FIPS set error: %d" % e.returncode)
            result["InfoMsg"] = "FIPS SET error"

        except FileNotFoundError:
            result["InfoMsg"] = "Not a FIPS image"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        except TimeoutExpired as e:
            syslog("FIPS SET timeout: %s" % e)
            result["InfoMsg"] = "FIPS SET timeout"

        except Exception as e:
            syslog("FIPS set exception: %s" % e)
            result["InfoMsg"] = "FIPS SET exception: {}".format(e)

        resp.media = result

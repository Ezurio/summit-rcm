import falcon
import os
from syslog import syslog, LOG_ERR
from subprocess import call
from .definition import (
    SUMMIT_RCM_ERRORS,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
)
from summit_rcm.services.system_service import SystemService
from summit_rcm.services.fips_service import FipsService


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
            await SystemService().set_power_state("off")

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
            await SystemService().set_power_state("suspend")

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
            await SystemService().set_power_state("reboot")

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

        if not await FipsService().set_fips_state(fips):
            result["InfoMsg"] = "FIPS SET error"
        else:
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

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

        result["status"] = await FipsService().get_fips_state()
        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        resp.media = result

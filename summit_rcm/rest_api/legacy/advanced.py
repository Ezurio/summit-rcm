"""
Module to support advanced configuration for legacy routes
"""

import falcon
import os
from syslog import syslog, LOG_ERR
from summit_rcm.definition import (
    SUMMIT_RCM_ERRORS,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
)
from summit_rcm.services.system_service import SystemService, FACTORY_RESET_SCRIPT
from summit_rcm.services.fips_service import FipsService


class PowerOff:
    """Resource to handler power off requests"""

    async def on_put(self, req, resp):
        """
        PUT handler for the /poweroff endpoint
        """
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
    """Resource to handler suspend requests"""

    async def on_put(self, req, resp):
        """
        PUT handler for the /suspend endpoint
        """
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
    """Resource to handler reboot requests"""

    async def on_put(self, req, resp):
        """
        PUT handler for the /reboot endpoint
        """
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
    """Resource to handler factory reset requests"""

    async def on_put(self, req, resp):
        """
        PUT handler for the /factoryReset endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "FactoryReset cannot be initiated",
        }

        if not os.path.exists(FACTORY_RESET_SCRIPT):
            result["InfoMsg"] += " - not available on non-encrypted file system images"
            resp.media = result
            return

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            resp.media = result
            return

        returncode: int = await SystemService().initiate_factory_reset()
        result["SDCERR"] = returncode
        if returncode == 0:
            result["InfoMsg"] = "Reboot required"
        else:
            result["InfoMsg"] = "Error running factory reset"
            syslog(f"FactoryReset returned {returncode}")

        resp.media = result


class Fips:
    """Resource to handler factory reset requests"""

    async def on_put(self, req, resp):
        """
        PUT handler for the /fips endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Reboot required",
        }

        set_options = ["unset", "fips", "fips_wifi"]

        post_data = await req.get_media()
        fips = post_data.get("fips", None)
        if fips not in set_options:
            result["InfoMsg"] = f"Invalid option: {fips}; valid options: {set_options}"
            resp.media = result
            return

        if not await FipsService().set_fips_state(fips):
            result["InfoMsg"] = "FIPS SET error"
        else:
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]

        resp.media = result

    async def on_get(self, req, resp):
        """
        GET handler for the /fips endpoint
        """
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

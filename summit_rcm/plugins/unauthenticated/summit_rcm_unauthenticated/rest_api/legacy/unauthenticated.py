"""
Module to support allowUnauthenticatedResetReboot for legacy routes
"""
from syslog import syslog, LOG_ERR

import falcon

from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm_unauthenticated.services.unauthenticated_service import (
    UnauthenticatedService,
)


class AllowUnauthenticatedResourceLegacy:
    """
    Resource to handle queries and requests for the allowUnauthenticatedResetReboot legacy endpoint
    """

    async def on_put(self, req, resp):
        """
        PUT handler for the allowUnauthenticatedResetReboot endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot set allow unauthenticated reset reboot",
        }

        try:
            if UnauthenticatedService().set_allow_unauthenticated_enabled(True):
                result["InfoMsg"] = ""
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        resp.media = result

    async def on_delete(self, req, resp):
        """
        DELETE handler for the allowUnauthenticatedResetReboot endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot clear allow unauthenticated reset reboot",
        }

        try:
            if UnauthenticatedService().set_allow_unauthenticated_enabled(False):
                result["InfoMsg"] = ""
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        resp.media = result

    async def on_get(self, req, resp):
        """
        GET handler for the allowUnauthenticatedResetReboot endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot read allow unauthenticated reset reboot",
        }

        try:
            result[
                "allowUnauthenticatedRebootReset"
            ] = UnauthenticatedService().get_allow_unauthenticated_enabled()
            result["InfoMsg"] = ""
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be read: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be read: {str(e)}"
            )
        resp.media = result

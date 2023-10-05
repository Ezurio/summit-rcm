"""
Module to handle log forwarding for legacy routes
"""

from syslog import LOG_ERR, syslog
import falcon
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm.systemd_unit import SYSTEMD_UNIT_VALID_CONFIG_STATES
from summit_rcm_log_forwarding.services.log_forwarding_service import (
    ActivationFailedError,
    AlreadyActiveError,
    AlreadyInactiveError,
    DeactivationFailedError,
    LogForwardingService,
)


class LogForwarding:
    """Resource to handle queries and requests for log forwarding"""

    async def on_get(self, _, resp):
        """
        GET handler for the /logForwarding endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not retrieve log forwarding state",
            "state": "unknown",
        }

        try:
            result["state"] = await LogForwardingService().get_active_state()
            if result["state"] != "unknown":
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = ""
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Could not retrieve log forwarding state: {str(exception)}",
            )

        resp.media = result

    async def on_put(self, req, resp):
        """
        PUT handler for the /logForwarding endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not set log forwarding state",
        }

        try:
            post_data = await req.get_media()
            requested_state = post_data.get("state", None)
            if not requested_state:
                result[
                    "InfoMsg"
                ] = f"Invalid state; valid states: {SYSTEMD_UNIT_VALID_CONFIG_STATES}"
                resp.media = result
                return
            if requested_state not in SYSTEMD_UNIT_VALID_CONFIG_STATES:
                result["InfoMsg"] = (
                    f"Invalid state: {requested_state}; "
                    f"valid states: {SYSTEMD_UNIT_VALID_CONFIG_STATES}"
                )
                resp.media = result
                return

            await LogForwardingService().set_state(requested_state)
            result["log_forwarding_state"] = await LogForwardingService().get_active_state()
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = ""
        except AlreadyActiveError:
            result["InfoMsg"] = "Log forwarding already active"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except AlreadyInactiveError:
            result["InfoMsg"] = "Log forwarding already inactive"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except ActivationFailedError:
            result["InfoMsg"] = "could not activate log forwarding service"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        except DeactivationFailedError:
            result["InfoMsg"] = "could not deactivate log forwarding service"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        except Exception as exception:
            syslog(LOG_ERR, f"Could not set log forwarding state: {str(exception)}")
            result = {
                "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set log forwarding state",
            }

        resp.media = result

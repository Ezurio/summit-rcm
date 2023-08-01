"""
Module to handle stunnel activate/deactivate for legacy routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm.stunnel.stunnel_service import StunnelService
from summit_rcm.systemd_unit import (
    SYSTEMD_UNIT_VALID_CONFIG_STATES,
    ActivationFailedError,
    AlreadyActiveError,
    AlreadyInactiveError,
    DeactivationFailedError,
)


class StunnelResourceLegacy:
    """
    Resource to expose stunnel status control
    """

    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /stunnel endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not retrieve stunnel state",
            "state": "unknown",
        }

        try:
            result["state"] = await StunnelService().get_active_state()
            if result["state"] != "unknown":
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = ""
        except Exception as exception:
            syslog(LOG_ERR, f"Could not retrieve stunnel state: {str(exception)}")

        resp.media = result

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /stunnel endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not set stunnel state",
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

            await StunnelService().set_state(requested_state)
            result["InfoMsg"] = ""
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except AlreadyActiveError:
            result["InfoMsg"] = "stunnel already active"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except AlreadyInactiveError:
            result["InfoMsg"] = "stunnel already inactive"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except ActivationFailedError:
            result["InfoMsg"] = "could not activate stunnel service"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        except DeactivationFailedError:
            result["InfoMsg"] = "could not deactivate stunnel service"
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        except Exception as exception:
            syslog(LOG_ERR, f"Could not set stunnel state: {str(exception)}")
            result = {
                "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set stunnel state",
            }

        resp.media = result

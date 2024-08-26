#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle stunnel activate/deactivate for legacy routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm_stunnel.services.stunnel_service import StunnelService
from summit_rcm.systemd_unit import (
    SYSTEMD_UNIT_VALID_CONFIG_STATES,
    ActivationFailedError,
    AlreadyActiveError,
    AlreadyInactiveError,
    DeactivationFailedError,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        DefaultResponseModelLegacy,
    )
    from summit_rcm_stunnel.rest_api.utils.spectree.models import (
        StunnelStateModel,
        StunnelStateModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    DefaultResponseModelLegacy = None
    StunnelStateModel = None
    StunnelStateModelLegacy = None
    network_tag = None


spec = SpectreeService()


class StunnelResourceLegacy:
    """
    Resource to expose stunnel status control
    """

    @spec.validate(
        resp=Response(
            HTTP_200=StunnelStateModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current stunnel state (legacy)
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

    @spec.validate(
        json=StunnelStateModel,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Update stunnel state (legacy)
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
                result["InfoMsg"] = (
                    f"Invalid state; valid states: {SYSTEMD_UNIT_VALID_CONFIG_STATES}"
                )
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

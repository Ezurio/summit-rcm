"""
Module to support allowUnauthenticatedResetReboot for legacy routes
"""

from syslog import syslog, LOG_ERR

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_unauthenticated.services.unauthenticated_service import (
    UnauthenticatedService,
)

from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm_unauthenticated.services.unauthenticated_service import (
    UnauthenticatedService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        DefaultResponseModelLegacy,
    )
    from summit_rcm_unauthenticated.rest_api.utils.spectree.models import (
        AllowUnauthenticatedRebootResetStateModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    DefaultResponseModelLegacy = None
    AllowUnauthenticatedRebootResetStateModelLegacy = None
    system_tag = None


spec = SpectreeService()


class AllowUnauthenticatedResourceLegacy:
    """
    Resource to handle queries and requests for the allowUnauthenticatedResetReboot legacy endpoint
    """

    @spec.validate(
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_put(self, req, resp):
        """
        Enable unauthenticated access to the reboot/reset endpoints (legacy)
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
            result["SDCERR"] = (
                f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            )
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        resp.media = result

    @spec.validate(
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_delete(self, req, resp):
        """
        Disable unauthenticated access to the reboot/reset endpoints (legacy)
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
            result["SDCERR"] = (
                f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            )
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        resp.media = result

    @spec.validate(
        resp=Response(
            HTTP_200=AllowUnauthenticatedRebootResetStateModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve the current state of the allowUnauthenticatedResetReboot setting (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot read allow unauthenticated reset reboot",
        }

        try:
            result["allowUnauthenticatedRebootReset"] = (
                UnauthenticatedService().get_allow_unauthenticated_enabled()
            )
            result["InfoMsg"] = ""
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result["SDCERR"] = (
                f"AllowUnauthenticatedRebootReset cannot be read: {str(e)}"
            )
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be read: {str(e)}"
            )
        resp.media = result

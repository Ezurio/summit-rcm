"""
Module to support configuration of AWM for legacy routes.
"""

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm import definition
from summit_rcm_awm.services.awm_config_service import AWMConfigService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_awm.rest_api.utils.spectree.models import (
        AWMStateResponseModelLegacy,
        AWMStateRequestModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    AWMStateResponseModelLegacy = None
    AWMStateRequestModelLegacy = None
    network_tag = None


spec = SpectreeService()


class AWMResourceLegacy:
    """
    Resource to expose AWM configuration
    """

    @spec.validate(
        resp=Response(
            HTTP_200=AWMStateResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve current AWM configuration (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        # Infinite geo-location checks by default
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "AWM configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        try:
            scan_attempts = AWMConfigService().get_scan_attempts()
        except Exception:
            resp.media = result
            return

        result["geolocation_scanning_enable"] = scan_attempts
        result["InfoMsg"] = ""
        resp.media = result

    @spec.validate(
        json=AWMStateRequestModelLegacy,
        resp=Response(
            HTTP_200=AWMStateResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_put(self, req, resp):
        """
        Set AWM configuration (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        # Enable/disable geolocation scanning
        # 0: disable geolocation scanning
        # others: enable geolocation scanning
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        if not AWMConfigService.get_lite_mode_enabled():
            resp.media = result
            return

        # prep for next error condition
        result["InfoMsg"] = "No writable configuration file found"

        put_data = await req.get_media()
        geolocation_scanning_enable = put_data.get("geolocation_scanning_enable", 0)

        try:
            AWMConfigService().set_scan_attempts(geolocation_scanning_enable)
        except Exception:
            resp.media = result
            return

        result["geolocation_scanning_enable"] = geolocation_scanning_enable
        result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        result["InfoMsg"] = ""
        resp.media = result

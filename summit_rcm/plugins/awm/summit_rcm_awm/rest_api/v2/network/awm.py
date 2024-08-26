#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support configuration of AWM for v2 routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_awm.services.awm_config_service import AWMConfigService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_awm.rest_api.utils.spectree.models import AWMStateResponseModel
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    AWMStateResponseModel = None
    network_tag = None


spec = SpectreeService()


class AWMResource(object):
    """
    Resource to handle queries and requests for AWM
    """

    async def get_awm_state(self) -> dict:
        """Retrieve a dictionary of the AWM geolocationScanningEnabled state"""
        result = {}
        try:
            result["geolocationScanningEnabled"] = (
                AWMConfigService().get_scan_attempts()
            )
        except Exception as exception:
            # Default to 1 (enabled) if there's an exception
            syslog(f"Unable to read AWM configuration: {str(exception)}")
            result["geolocationScanningEnabled"] = 1

        return result

    @spec.validate(
        resp=Response(
            HTTP_200=AWMStateResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current AWM configuration
        """
        try:
            resp.media = await self.get_awm_state()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve AWM Configuration: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=AWMStateResponseModel,
        resp=Response(
            HTTP_200=AWMStateResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Set AWM configuration
        """
        try:
            # Parse inputs
            put_data: dict = await req.get_media()

            if AWMConfigService.get_lite_mode_enabled():
                try:
                    geolocation_scanning_enable = int(
                        put_data.get("geolocationScanningEnabled", 0)
                    )
                except Exception:
                    resp.status = falcon.HTTP_400
                    return
            else:
                geolocation_scanning_enable = None

            # Handle new inputs
            if geolocation_scanning_enable is not None:
                try:
                    AWMConfigService().set_scan_attempts(geolocation_scanning_enable)
                except Exception as exception:
                    syslog(f"Unable to configure AWM: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

            # Prepare response
            resp.media = await self.get_awm_state()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to configure AWM: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

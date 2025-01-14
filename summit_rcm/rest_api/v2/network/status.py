#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle network status info
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.network_service import NetworkService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        InternalServerErrorResponseModel,
        NetworkStatusResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    NetworkStatusResponseModel = None
    InternalServerErrorResponseModel = None
    network_tag = None


spec = SpectreeService()


class NetworkStatusResource(object):
    """
    Resource to handle network status queries and requests
    """

    @spec.validate(
        resp=Response(
            HTTP_200=NetworkStatusResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve network status info
        """
        try:
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON

            result = {}
            result["status"] = await NetworkService.get_status(is_legacy=False)

            unmanaged_devices = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "unmanaged_hardware_devices", fallback="")
                .split()
            )
            for dev in unmanaged_devices:
                if dev in result["status"]:
                    del result["status"][dev]
            result["devices"] = len(result["status"])
            resp.media = result
        except Exception as e:
            syslog(LOG_ERR, f"Could not retrieve network status - {str(e)}")
            resp.status = falcon.HTTP_500

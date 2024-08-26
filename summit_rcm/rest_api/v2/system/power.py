#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to interact with system power states
"""

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import PowerStateEnum
from summit_rcm.services.system_service import SystemService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        PowerState,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    PowerState = None
    UnauthorizedErrorResponseModel = None
    system_tag = None


spec = SpectreeService()


class PowerResource(object):
    """
    Resource to handle power state queries and requests
    """

    @spec.validate(
        resp=Response(
            HTTP_200=PowerState,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """Retrieve current power state"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"state": SystemService().power_state}

    @spec.validate(
        json=PowerState,
        resp=Response(
            HTTP_200=PowerState,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """Set the desired power state"""
        post_data = await req.get_media()
        try:
            desired_state = PowerStateEnum(post_data.get("state", ""))
        except ValueError:
            resp.status = falcon.HTTP_400
            return

        await SystemService().set_power_state(desired_state)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"state": SystemService().power_state}

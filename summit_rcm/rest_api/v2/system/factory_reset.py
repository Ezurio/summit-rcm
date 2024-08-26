#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle system factory reset
"""

import asyncio
import os
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE, PowerStateEnum
from summit_rcm.services.system_service import SystemService, FACTORY_RESET_SCRIPT

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        FactoryResetModel,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    FactoryResetModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    system_tag = None


spec = SpectreeService()


class FactoryResetResource(object):
    """
    Resource to handle factory reset requests
    """

    @spec.validate(
        json=FactoryResetModel,
        resp=Response(
            HTTP_200=FactoryResetModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Initiate a factory reset
        """

        post_data = await req.get_media()
        initiate_factory_reset = post_data.get("initiateFactoryReset", None)
        auto_reboot = post_data.get("autoReboot", None)

        if initiate_factory_reset is None or auto_reboot is None:
            resp.status = falcon.HTTP_400
            return

        initiate_factory_reset = bool(initiate_factory_reset)
        auto_reboot = bool(auto_reboot)

        if not initiate_factory_reset:
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.media = {"initiateFactoryReset": False, "autoReboot": False}
            return

        if not os.path.exists(FACTORY_RESET_SCRIPT):
            resp.status = falcon.HTTP_500
            return

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            resp.status = falcon.HTTP_500
            return

        returncode: int = await SystemService().initiate_factory_reset()

        if returncode != 0:
            resp.status = falcon.HTTP_500
            return

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            "initiateFactoryReset": initiate_factory_reset,
            "autoReboot": auto_reboot,
        }

        if auto_reboot:
            asyncio.ensure_future(
                SystemService().set_power_state(PowerStateEnum.REBOOT)
            )

#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support allowUnauthenticatedResetReboot for v2 routes
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

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_unauthenticated.rest_api.utils.spectree.models import (
        AllowUnauthenticatedRebootResetStateModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    AllowUnauthenticatedRebootResetStateModel = None
    system_tag = None


spec = SpectreeService()


class AllowUnauthenticatedResource:
    """
    Resource to handle queries and requests for the /system/allowUnauthenticatedResetReboot v2
    endpoint
    """

    @spec.validate(
        resp=Response(
            HTTP_200=None,
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
        Enable unauthenticated access to the reboot/reset endpoints
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        try:
            UnauthenticatedService().set_allow_unauthenticated_enabled(True)
        except Exception as e:
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_delete(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Disable unauthenticated access to the reboot/reset endpoints
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        try:
            UnauthenticatedService().set_allow_unauthenticated_enabled(False)
        except Exception as e:
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        resp=Response(
            HTTP_200=AllowUnauthenticatedRebootResetStateModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        Retrieve the current state of the allowUnauthenticatedResetReboot setting
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        try:
            resp.media = {
                "allowUnauthenticatedRebootReset": UnauthenticatedService().get_allow_unauthenticated_enabled()
            }
        except Exception as e:
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be read: {str(e)}"
            )
            resp.status = falcon.HTTP_500

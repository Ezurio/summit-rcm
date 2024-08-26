#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support NTP configuration via chrony for v2 routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_chrony.services.ntp_service import (
    REMOVE_SOURCE,
    OVERRIDE_SOURCES,
    ChronyNTPService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        NotFoundErrorResponseModel,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_chrony.rest_api.utils.spectree.models import (
        ChronySourcesResponseModel,
        ChronySourceModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    NotFoundErrorResponseModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    ChronySourcesResponseModel = None
    ChronySourceModel = None
    system_tag = None


spec = SpectreeService()


class NTPSourcesResource:
    """
    Resource to handle queries and requests for chrony NTP sources
    """

    @spec.validate(
        resp=Response(
            HTTP_200=ChronySourcesResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        Retrieve chrony NTP sources
        """
        try:
            resp.media = await ChronyNTPService.chrony_get_sources()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve chrony NTP sources: {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ChronySourcesResponseModel,
        resp=Response(
            HTTP_200=ChronySourcesResponseModel,
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
        Update chrony NTP sources
        """
        try:
            put_data = await req.get_media(default_when_empty=None)
            if put_data is None or not isinstance(put_data, list):
                resp.status = falcon.HTTP_400
                return

            new_sources: list[str] = []
            for source in put_data:
                if not isinstance(source, dict):
                    resp.status = falcon.HTTP_400
                    return

                source_keys = source.keys()
                if "address" not in source_keys or "type" not in source_keys:
                    resp.status = falcon.HTTP_400
                    return

                # Only 'static' sources (e.g., sources not configured via DHCP) can be configured
                if source["type"] == "static":
                    new_sources.append(str(source["address"]))
            await ChronyNTPService.chrony_configure_sources(
                OVERRIDE_SOURCES, new_sources
            )

            resp.media = await ChronyNTPService.chrony_get_sources()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to configure chrony NTP sources: {str(exception)}")
            resp.status = falcon.HTTP_500


class NTPSourceResource:
    """
    Resource to handle queries and requests for a specific chrony NTP source by address
    """

    @spec.validate(
        resp=Response(
            HTTP_200=ChronySourceModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        path_parameter_descriptions={"address": "The address of the NTP source"},
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _, resp: falcon.asgi.Response, address: str) -> None:
        """
        Retrieve a specific chrony NTP source by address
        """
        try:
            if not address:
                resp.status = falcon.HTTP_400
                return

            for source in await ChronyNTPService.chrony_get_sources():
                if source["address"] == address:
                    resp.media = {"address": source["address"], "type": source["type"]}
                    resp.status = falcon.HTTP_200
                    resp.content_type = falcon.MEDIA_JSON
                    return

            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve chrony NTP source: {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        path_parameter_descriptions={"address": "The address of the NTP source"},
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, address: str
    ) -> None:
        """
        Remove a specific chrony NTP source by address
        """
        try:
            if not address:
                resp.status = falcon.HTTP_400
                return

            for source in await ChronyNTPService.chrony_get_sources():
                # Only 'static' sources (e.g., sources not configured via DHCP) can be removed
                if source["address"] == address and source["type"] == "static":
                    await ChronyNTPService.chrony_configure_sources(
                        REMOVE_SOURCE, [source["address"]]
                    )
                    resp.status = falcon.HTTP_200
                    return

            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to remove chrony NTP source: {str(exception)}")
            resp.status = falcon.HTTP_500

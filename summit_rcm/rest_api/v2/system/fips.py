"""
Module to support FIPS configuration for v2 routes
"""

import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.fips_service import FipsService, VALID_FIPS_STATES

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        FIPSModel,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    FIPSModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    system_tag = None


spec = SpectreeService()


class FipsResource(object):
    """
    Resource to handle FIPS state queries and requests
    """

    @spec.validate(
        resp=Response(
            HTTP_200=FIPSModel,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current FIPS state
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        fips_state = await FipsService().get_fips_state()

        # Change from snake case to camel case for the 'fips_wifi' case
        if fips_state == "fips_wifi":
            fips_state = "fipsWifi"

        resp.media = {"state": fips_state}

    @spec.validate(
        json=FIPSModel,
        resp=Response(
            HTTP_200=FIPSModel,
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
        Set desired FIPS state
        """
        post_data = await req.get_media()
        desired_state = str(post_data.get("state", ""))

        # Change from camel case to snake case for the 'fipsWifi' case
        if desired_state == "fipsWifi":
            desired_state = "fips_wifi"

        if desired_state == "" or desired_state not in VALID_FIPS_STATES:
            resp.status = falcon.HTTP_400
            return

        success: bool = await FipsService().set_fips_state(desired_state)

        new_fips_state = await FipsService().get_fips_state()

        # Change from snake case to camel case for the 'fips_wifi' case
        if new_fips_state == "fips_wifi":
            new_fips_state = "fipsWifi"

        resp.status = falcon.HTTP_200 if success else falcon.HTTP_500
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"state": new_fips_state}

"""
Module to interact with access points
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
        AccessPointScanRequestReponseModel,
        AccessPoints,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    AccessPointScanRequestReponseModel = None
    AccessPoints = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    network_tag = None


spec = SpectreeService()


class AccessPointsResource:
    """
    Resource to handle queries and requests for access points
    """

    @spec.validate(
        resp=Response(
            HTTP_200=AccessPoints,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve a list of known access points
        """
        try:
            resp.media = await NetworkService.get_access_points(is_legacy=False)
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve list of access points: {str(exception)}",
            )
            resp.status = falcon.HTTP_500


class AccessPointsScanResource:
    """
    Resource to handle queries and requests for access point scanning
    """

    @spec.validate(
        resp=Response(
            HTTP_200=AccessPointScanRequestReponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=AccessPointScanRequestReponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Request an access point scan
        """
        try:
            await NetworkService.request_ap_scan()
            resp.media = {"scanRequested": True}
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to initiate access point scan: {str(exception)}",
            )
            resp.media = {"scanRequested": False}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_500

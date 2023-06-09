"""
Module to interact with access points
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.services.network_service import NetworkService


class AccessPointsResource:
    """
    Resource to handle queries and requests for access points
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/accessPoints endpoint
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

    async def on_put(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        PUT handler for the /network/accessPoints/scan endpoint
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

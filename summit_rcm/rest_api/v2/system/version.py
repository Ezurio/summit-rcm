"""
Module to handle version requests
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.services.version_service import VersionService


class VersionResource:
    """
    Resource to handle queries and requests for version info
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/version endpoint
        """
        try:
            version = await VersionService().get_version(is_legacy=False)
            if not version:
                raise Exception("no version info found")

            resp.media = version
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not get current system version info - {str(exception)}")
            resp.status = falcon.HTTP_500

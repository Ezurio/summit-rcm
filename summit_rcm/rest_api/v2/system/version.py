"""
Module to handle version requests
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.version_service import VersionService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
        VersionInfo,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    VersionInfo = None
    system_tag = None


spec = SpectreeService()


class VersionResource:
    """
    Resource to handle queries and requests for version info
    """

    @spec.validate(
        resp=Response(
            HTTP_200=VersionInfo,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve version info
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

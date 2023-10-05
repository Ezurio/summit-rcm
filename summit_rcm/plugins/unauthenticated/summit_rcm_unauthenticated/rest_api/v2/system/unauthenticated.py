"""
Module to support allowUnauthenticatedResetReboot for v2 routes
"""
from syslog import syslog, LOG_ERR
import falcon.asgi
from summit_rcm_unauthenticated.services.unauthenticated_service import (
    UnauthenticatedService,
)


class AllowUnauthenticatedResource:
    """
    Resource to handle queries and requests for the /system/allowUnauthenticatedResetReboot v2
    endpoint
    """

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /system/allowUnauthenticatedResetReboot endpoint
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

    async def on_delete(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        DELETE handler for the /system/allowUnauthenticatedResetReboot endpoint
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

    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/allowUnauthenticatedResetReboot endpoint
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

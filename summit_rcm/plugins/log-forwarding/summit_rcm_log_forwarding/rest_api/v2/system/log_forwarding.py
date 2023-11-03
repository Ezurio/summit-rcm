"""
Module to interact with log forwarding
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.systemd_unit import SYSTEMD_UNIT_VALID_CONFIG_STATES
from summit_rcm_log_forwarding.services.log_forwarding_service import (
    AlreadyActiveError,
    AlreadyInactiveError,
    LogForwardingService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        InternalServerErrorResponseModel,
        BadRequestErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_log_forwarding.rest_api.utils.spectree.models import (
        LogForwardingStateModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    InternalServerErrorResponseModel = None
    BadRequestErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    LogForwardingStateModel = None
    system_tag = None


spec = SpectreeService()


class LogForwardingResource:
    """
    Resource to handle queries and requests for log forwarding
    """

    @spec.validate(
        resp=Response(
            HTTP_200=LogForwardingStateModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current log forwarding state
        """
        try:
            resp.media = {"state": await LogForwardingService().get_active_state()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not retrieve log forwarding state - {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=LogForwardingStateModel,
        resp=Response(
            HTTP_200=LogForwardingStateModel,
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
        Update log forwarding state
        """
        try:
            put_data = await req.get_media()

            # Read in and validate the input data
            requested_state = put_data.get("state", None)
            if (
                not requested_state
                or requested_state not in SYSTEMD_UNIT_VALID_CONFIG_STATES
            ):
                raise ValueError()

            # Configure new value
            try:
                await LogForwardingService().set_state(requested_state)
            except (AlreadyActiveError, AlreadyInactiveError):
                # We can safely ignore the errors where the service is already in the requested
                # state
                pass

            # Return newly-set current configuration
            resp.media = {"state": await LogForwardingService().get_active_state()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ValueError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(f"Could not set log forwarding state - {str(exception)}")
            resp.status = falcon.HTTP_500

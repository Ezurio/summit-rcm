"""
Module to support stunnel configuration for v2 routes.
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_stunnel.services.stunnel_service import StunnelService
from summit_rcm.systemd_unit import (
    SYSTEMD_UNIT_VALID_CONFIG_STATES,
    AlreadyActiveError,
    AlreadyInactiveError,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_stunnel.rest_api.utils.spectree.models import StunnelStateModel
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    StunnelStateModel = None
    network_tag = None


spec = SpectreeService()


class StunnelResource:
    """
    Resource to handle queries and requests for stunnel service configuration
    """

    @spec.validate(
        resp=Response(
            HTTP_200=StunnelStateModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current stunnel state
        """
        try:
            resp.media = {"state": await StunnelService().get_active_state()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not retrieve stunnel state - {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=StunnelStateModel,
        resp=Response(
            HTTP_200=StunnelStateModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Update stunnel state
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
                await StunnelService().set_state(requested_state)
            except (AlreadyActiveError, AlreadyInactiveError):
                # We can safely ignore the errors where the service is already in the requested
                # state
                pass

            # Return newly-set current configuration
            resp.media = {"state": await StunnelService().get_active_state()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ValueError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(f"Could not set stunnel state - {str(exception)}")
            resp.status = falcon.HTTP_500

"""
Module to support stunnel configuration for v2 routes.
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.stunnel.stunnel_service import StunnelService
from summit_rcm.systemd_unit import (
    SYSTEMD_UNIT_VALID_CONFIG_STATES,
    AlreadyActiveError,
    AlreadyInactiveError,
)


class StunnelResource:
    """
    Resource to handle queries and requests for stunnel service configuration
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/stunnel endpoint
        """
        try:
            resp.media = {"state": await StunnelService().get_active_state()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not retrieve stunnel state - {str(exception)}")
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /system/stunnel endpoint
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

"""
Module to support configuration of AWM for v2 routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm_awm.services.awm_config_service import AWMConfigService


class AWMResource(object):
    """
    Resource to handle queries and requests for AWM
    """

    async def get_awm_state(self) -> dict:
        """Retrieve a dictionary of the AWM geolocationScanningEnabled state"""
        result = {}
        try:
            result[
                "geolocationScanningEnabled"
            ] = AWMConfigService().get_scan_attempts()
        except Exception as exception:
            # Default to 1 (enabled) if there's an exception
            syslog(f"Unable to read AWM configuration: {str(exception)}")
            result["geolocationScanningEnabled"] = 1

        return result

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/wifi/awm endpoint
        """
        try:
            resp.media = await self.get_awm_state()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve AWM Configuration: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /network/wifi/awm endpoint
        """
        try:
            # Parse inputs
            put_data: dict = await req.get_media()

            if AWMConfigService.get_lite_mode_enabled():
                try:
                    geolocation_scanning_enable = int(
                        put_data.get("geolocationScanningEnabled", 0)
                    )
                except Exception:
                    resp.status = falcon.HTTP_400
                    return
            else:
                geolocation_scanning_enable = None

            # Handle new inputs
            if geolocation_scanning_enable is not None:
                try:
                    AWMConfigService().set_scan_attempts(geolocation_scanning_enable)
                except Exception as exception:
                    syslog(f"Unable to configure AWM: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

            # Prepare response
            resp.media = await self.get_awm_state()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to configure AWM: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

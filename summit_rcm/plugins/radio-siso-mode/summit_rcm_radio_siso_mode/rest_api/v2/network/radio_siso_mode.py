"""
Module to support configuration of the radio's SISO mode parameter for v2 routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm_radio_siso_mode.services.radio_siso_mode_service import (
    RadioSISOModeService,
)


class RadioSISOModeResource(object):
    """
    Resource to handle queries and requests for the radio's SISO mode
    """

    async def get_siso_mode(self) -> dict:
        """Retrieve a dictionary of the radio's SISO mode"""
        result = {}
        try:
            result["sisoMode"] = RadioSISOModeService.get_current_siso_mode()
        except Exception as exception:
            # Default to -1 (system default) if there's an exception
            syslog(f"Unable to read SISO mode parameter: {str(exception)}")
            result["sisoMode"] = -1

        return result

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/wifi/radioSISOMode endpoint
        """
        try:
            resp.media = await self.get_siso_mode()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to retrieve radio SISO mode: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /network/wifi/radioSISOMode endpoint
        """
        try:
            # Parse inputs
            put_data: dict = await req.get_media()
            try:
                siso_mode = int(put_data.get("sisoMode", None))
                if siso_mode is None:
                    raise Exception("Invalid parameter")
            except Exception:
                resp.status = falcon.HTTP_400
                return

            # Handle new inputs
            if siso_mode != RadioSISOModeService.get_current_siso_mode():
                try:
                    RadioSISOModeService.set_siso_mode(siso_mode)
                except Exception as exception:
                    syslog(f"Unable to configure SISO mode parameter: {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

            # Prepare response
            resp.media = await self.get_siso_mode()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Unable to configure radio's SISO Mode: {str(exception)}",
            )
            resp.status = falcon.HTTP_500

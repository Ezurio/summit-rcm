"""
Module to support configuration of the radio's SISO mode parameter for v2 routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_radio_siso_mode.services.radio_siso_mode_service import (
    RadioSISOModeEnum,
    RadioSISOModeService,
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
    from summit_rcm_radio_siso_mode.rest_api.utils.spectree.models import (
        SISOModeStateModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    SISOModeStateModel = None
    network_tag = None


spec = SpectreeService()


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

    @spec.validate(
        resp=Response(
            HTTP_200=SISOModeStateModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve the current radio SISO mode configuration
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

    @spec.validate(
        json=SISOModeStateModel,
        resp=Response(
            HTTP_200=SISOModeStateModel,
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
        Update the radio's SISO mode configuration
        """
        try:
            # Parse inputs
            put_data: dict = await req.get_media()
            try:
                siso_mode = RadioSISOModeEnum(put_data.get("sisoMode", None))
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

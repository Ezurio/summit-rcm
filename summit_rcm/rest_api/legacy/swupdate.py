"""
Module to handle legacy firmware updates via swupdate
"""

from syslog import syslog, LOG_ERR
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.firmware_update_service import (
    NoUpdateInProgressError,
    UpdateError,
)
from summit_rcm.rest_api.services.rest_firmware_update_service import (
    RESTFirmwareUpdateService as FirmwareUpdateService,
    MEDIA_OCTET_STREAM,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        LengthRequiredErrorResponseModel,
        UnsupportedMediaTypeErrorResponseModel,
        InternalServerErrorResponseModel,
        DefaultResponseModelLegacy,
        FirmwareUpdateModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    LengthRequiredErrorResponseModel = None
    UnsupportedMediaTypeErrorResponseModel = None
    InternalServerErrorResponseModel = None
    DefaultResponseModelLegacy = None
    FirmwareUpdateModelLegacy = None
    system_tag = None


spec = SpectreeService()


class SWUpdate(object):
    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_411=LengthRequiredErrorResponseModel,
            HTTP_415=UnsupportedMediaTypeErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_put(self, req: falcon.asgi.Request, resp: falcon.asgi.Response):
        """Upload firmware update file as an octet stream (legacy)"""
        resp.status = falcon.HTTP_200

        if not req.content_type or MEDIA_OCTET_STREAM not in req.content_type:
            resp.status = falcon.HTTP_415
            resp.text = "Expected an application/octet-stream content type"
            return

        if not req.content_length:
            resp.status = falcon.HTTP_411
            return

        try:
            await FirmwareUpdateService().handle_update_file_upload_stream(req.stream)
        except NoUpdateInProgressError:
            syslog(LOG_ERR, "swupdate.py: no update in progress")
            resp.status = falcon.HTTP_500
            resp.text = "Software Update error: no update in progress"
        except UpdateError as error:
            syslog(
                LOG_ERR,
                f"swclient.do_firmware_update returned {error.return_code} "
                "while processing octet stream",
            )
            resp.status = falcon.HTTP_500
            resp.text = (
                f"Software Update received error: {error.return_code} while updating"
            )
        except Exception as exception:
            syslog(LOG_ERR, f"Software Update error: {str(exception)}")
            resp.status = falcon.HTTP_500
            resp.text = f"Software Update error: {str(exception)}"

    @spec.validate(
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """Retrieve the current update status (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 1, "InfoMsg": "Device is busy"}

        try:
            (
                result["SDCERR"],
                result["InfoMsg"],
            ) = FirmwareUpdateService().get_update_status()
        except Exception as exception:
            syslog(LOG_ERR, str(exception))
            result["InfoMsg"] = f"Error: {str(exception)}"

        resp.media = result

    @spec.validate(
        json=FirmwareUpdateModelLegacy,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_post(self, req, resp):
        """Start a firmware update (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

        result = {
            "SDCERR": 1,
            "InfoMsg": "Device is busy updating.",
        }

        if FirmwareUpdateService().update_in_progress:
            resp.media = result
            return

        post_data = await req.get_media()
        url = post_data.get("url", None)
        if url and " " in url:
            result["InfoMsg"] = "Invalid URL"
            resp.media = result
            return
        image = post_data.get("image", "main")

        try:
            FirmwareUpdateService().start_update(url, image)
            result["InfoMsg"] = ""
            result["SDCERR"] = 0
        except Exception as exception:
            syslog(LOG_ERR, str(exception))
            result["InfoMsg"] = str(exception)
            FirmwareUpdateService().cancel_update()

        resp.media = result

    @spec.validate(
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
        deprecated=True,
    )
    async def on_delete(self, req, resp):
        """Cancel an in-progress firmware update (legacy)"""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {"SDCERR": 0, "InfoMsg": ""}
        try:
            FirmwareUpdateService().cancel_update()
        except Exception as exception:
            syslog(LOG_ERR, str(exception))
            result["SDCERR"] = 1
            result["InfoMsg"] = str(exception)
        resp.media = result

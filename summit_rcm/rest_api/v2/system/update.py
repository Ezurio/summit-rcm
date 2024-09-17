#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to facilitate firmware updates
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.firmware_update_service import (
    NoUpdateInProgressError,
    SummitRCMUpdateStatus,
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
        BadRequestErrorResponseModel,
        FirmwareUpdateStatus,
        InternalServerErrorResponseModel,
        LengthRequiredErrorResponseModel,
        UnauthorizedErrorResponseModel,
        UnsupportedMediaTypeErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    FirmwareUpdateStatus = None
    InternalServerErrorResponseModel = None
    LengthRequiredErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    UnsupportedMediaTypeErrorResponseModel = None
    system_tag = None


spec = SpectreeService()


class FirmwareUpdateStatusResource:
    """
    Resource to handle queries and requests for system update status
    """

    def get_current_update_status(self) -> dict:
        """Retrieve the current update status (internal)"""

        status, _ = FirmwareUpdateService().get_update_status()
        result = {
            "status": status,
            "url": FirmwareUpdateService().url,
            "image": FirmwareUpdateService().image,
        }

        return result

    @spec.validate(
        resp=Response(
            HTTP_200=FirmwareUpdateStatus,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve the current update status

        Valid <code>status</code> values are:
        <ul>
            <li>0 - Updated</li>
            <li>1 - Fail</li>
            <li>2 - Not updating</li>
            <li>5 - Updating</li>
        </ul>
        """
        try:
            resp.media = self.get_current_update_status()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not get current system update status - {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=FirmwareUpdateStatus,
        resp=Response(
            HTTP_200=FirmwareUpdateStatus,
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
        Set the desired update status (initiate/cancel update)

        This endpoint allows for initiating or cancelling a system update by setting the desired
        status. Valid <code>status</code> values are:
        <ul>
            <li>0 - Updated</li>
            <li>1 - Fail</li>
            <li>2 - Not updating</li>
            <li>5 - Updating</li>
        </ul>

        However, it is only possible to request a <code>status</code> of <code>2</code> (Not
        updating) or <code>5</code> (Updating).

        To initiate an update, populate the request body with a <code>status</code> value of
        <code>5</code> (Updating), as well as the <code>url</code> and <code>image</code> fields
        with appropriate values. The optional <code>url</code> field should contain the URL of the
        update (if pulling the update from a remote location), and the optional <code>image</code>
        field should contain the desired software update image (e.g., "main", "complete", etc.) to
        use (the default is "main" if omitted).

        Once the update is initiated, POST the software update file itself to the
        <a href="#tag/system/post/api/v2/system/update/updateFile"><code>updateFile</code></a>
        endpoint.

        To cancel an in-progress update, populate the request body with a <code>status</code> value
        of <code>2</code> (Not updating).
        """
        try:
            put_data = await req.get_media()
            desired_status = int(
                put_data.get("status", SummitRCMUpdateStatus.NOT_UPDATING)
            )

            if (
                desired_status == SummitRCMUpdateStatus.UPDATED
                or desired_status == SummitRCMUpdateStatus.FAIL
            ):
                resp.status = falcon.HTTP_400
                return

            url = str(put_data.get("url", ""))
            if url and " " in url:
                resp.status = falcon.HTTP_400
                return

            image = str(put_data.get("image", "main"))

            if desired_status == SummitRCMUpdateStatus.UPDATING:
                await FirmwareUpdateService().start_update(url=url, image=image)
            elif desired_status == SummitRCMUpdateStatus.NOT_UPDATING:
                try:
                    FirmwareUpdateService().cancel_update()
                except Exception:
                    pass

            resp.media = self.get_current_update_status()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not set current system update status - {str(exception)}")
            resp.status = falcon.HTTP_500


class FirmwareUpdateFileResource:
    """
    Resource to handle queries and requests for system update file upload
    """

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_411=LengthRequiredErrorResponseModel,
            HTTP_415=UnsupportedMediaTypeErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Upload update file
        """
        try:
            if not req.content_type or MEDIA_OCTET_STREAM not in req.content_type:
                resp.status = falcon.HTTP_415
                return

            if not req.content_length:
                resp.status = falcon.HTTP_411
                return

            await FirmwareUpdateService().handle_update_file_upload_stream(req.stream)
            resp.status = falcon.HTTP_200
        except NoUpdateInProgressError:
            resp.status = falcon.HTTP_400
        except UpdateError as error:
            syslog(
                f"Error from swupdate while processing octet stream - {error.return_code}"
            )
            resp.status = falcon.HTTP_500
        except Exception as exception:
            syslog(f"Error during software update - {str(exception)}")
            resp.status = falcon.HTTP_500

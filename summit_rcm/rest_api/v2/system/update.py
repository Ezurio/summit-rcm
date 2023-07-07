"""
Module to facilitate firmware updates
"""

from syslog import syslog
import falcon.asgi
from summit_rcm.services.firmware_update_service import (
    MEDIA_OCTET_STREAM,
    FirmwareUpdateService,
    NoUpdateInProgressError,
    SummitRCMUpdateStatus,
    UpdateError,
)


class FirmwareUpdateStatusResource:
    """
    Resource to handle queries and requests for system update status
    """

    def get_current_update_status(self) -> dict:
        """Retrieve the current update status"""

        status, _ = FirmwareUpdateService().get_update_status()
        result = {
            "status": status,
            "url": FirmwareUpdateService().url,
            "image": FirmwareUpdateService().image,
        }

        return result

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/update endpoint
        """
        try:
            resp.media = self.get_current_update_status()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not get current system update status - {str(exception)}")
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /system/update endpoint
        """
        try:
            put_data = await req.get_media()
            desired_status = int(put_data.get("status", SummitRCMUpdateStatus.NOT_UPDATING))

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
                FirmwareUpdateService().start_update(url=url, image=image)
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

    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        POST handler for the /system/update/updateFile endpoint
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

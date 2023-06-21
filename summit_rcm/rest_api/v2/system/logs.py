"""
Module to interact with system logs
"""

import os
from syslog import syslog
import falcon.asgi
from summit_rcm.services.files_service import FilesService


class LogsExportResource:
    """
    Resource to handle queries and requests for exporting logs
    """

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        GET handler for the /system/logs/export endpoint
        """
        archive = ""
        try:
            get_data = await req.get_media()
            password = get_data.get("password", "")
            if not password:
                resp.status = falcon.HTTP_400
                return

            success, msg, archive = FilesService.export_logs(password)
            if not success:
                raise Exception(msg)

            resp.stream = await FilesService.handle_file_download(archive)
            resp.content_type = falcon.MEDIA_TEXT
            resp.status = 200
        except Exception as exception:
            syslog(f"Could not export logs - {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            if os.path.isfile(archive):
                os.unlink(archive)

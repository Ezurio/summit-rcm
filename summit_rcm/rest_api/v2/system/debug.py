"""
Module to interact with system debug info
"""

import os
from syslog import syslog
import falcon.asgi
from summit_rcm.services.files_service import FilesService


class DebugExportResource:
    """
    Resource to handle queries and requests for exporting system debug info
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/debug/export endpoint
        """
        archive = ""
        try:
            success, msg, archive = FilesService.export_debug()
            if not success:
                raise Exception(msg)

            resp.stream = await FilesService.handle_file_download(archive)
            resp.content_type = falcon.MEDIA_TEXT
            resp.status = 200
        except Exception as exception:
            syslog(f"Could not export debug info - {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            if os.path.isfile(archive):
                os.unlink(archive)

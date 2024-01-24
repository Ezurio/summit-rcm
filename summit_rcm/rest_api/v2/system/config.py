"""
Module to interact with system config files
"""

import os
from syslog import syslog
import falcon.asgi
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)


class SystemConfigExportResource:
    """
    Resource to handle queries and requests for exporting system configuration files
    """

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        GET handler for the /system/config/export endpoint
        """
        archive = ""
        try:
            get_data = await req.get_media()
            password = get_data.get("password", "")
            if not password:
                resp.status = falcon.HTTP_400
                return

            success, msg, archive = await FilesService.export_system_config(password)
            if not success:
                raise Exception(msg)

            resp.stream = await FilesService.handle_file_download(archive)
            resp.content_type = falcon.MEDIA_TEXT
            resp.status = 200
        except Exception as exception:
            syslog(f"Could not export system config - {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            if os.path.isfile(archive):
                os.unlink(archive)


class SystemConfigImportResource:
    """Resource to handle queries and requests for importing system configuration files"""

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /system/config/import endpoint
        """
        try:
            password = ""
            form = await req.get_media()
            if not isinstance(form, falcon.asgi.multipart.MultipartForm):
                resp.status = falcon.HTTP_400
                return

            async for part in form:
                if part.name == "archive":
                    if not await FilesService.handle_config_import_file_upload_multipart_form(
                        part
                    ):
                        raise Exception("error uploading file")
                elif part.name == "password":
                    password = str(await part.text)

            if not password:
                resp.status = falcon.HTTP_400
                return

            success, msg = await FilesService.import_system_config(password)
            if not success:
                raise Exception(msg)
            resp.status = 200
        except Exception as exception:
            syslog(f"Could not import system configuration - {str(exception)}")
            resp.status = falcon.HTTP_500

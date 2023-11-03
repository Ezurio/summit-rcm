"""
Module to interact with system config files
"""

import os
from syslog import syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        InternalServerErrorResponseModel,
        SystemConfigExportRequestModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    SystemConfigExportRequestModel = None
    UnauthorizedErrorResponseModel = None
    system_tag = None


spec = SpectreeService()


class SystemConfigExportResource:
    """
    Resource to handle queries and requests for exporting system configuration files
    """

    @spec.validate(
        json=SystemConfigExportRequestModel,
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Retrieve an export of the current system configuration
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
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not export system config - {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            if os.path.isfile(archive):
                os.unlink(archive)


class SystemConfigImportResource:
    """Resource to handle queries and requests for importing system configuration files"""

    @spec.validate(
        resp=Response(
            HTTP_200=None,
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
        Import a previously-saved system configuration
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
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not import system configuration - {str(exception)}")
            resp.status = falcon.HTTP_500

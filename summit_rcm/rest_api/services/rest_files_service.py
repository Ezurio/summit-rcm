"""
Module to interact with files for the REST API
"""

from pathlib import Path
import falcon.asgi.multipart
from summit_rcm.services.files_service import (
    CONFIG_TMP_ARCHIVE_FILE,
    CONNECTION_TMP_ARCHIVE_FILE,
    FILE_READ_SIZE,
    NETWORKMANAGER_DIR_FULL,
    FilesService,
)
from summit_rcm.utils import Singleton


class RESTFilesService(FilesService, metaclass=Singleton):
    """
    Service to interact with files for the REST API
    """

    @staticmethod
    async def handle_file_upload_multipart_form_part(
        part: falcon.asgi.multipart.BodyPart, path: str, mode: str = "wb"
    ) -> str:
        """
        Handle file upload as multipart form part
        """
        with open(path, mode) as dest:
            while True:
                data = await part.stream.read(FILE_READ_SIZE)
                if not data:
                    break
                dest.write(data)
        return path

    @staticmethod
    async def handle_cert_file_upload_multipart_form(
        incoming_data: falcon.asgi.multipart.BodyPart,
        name: str,
        mode: str = "wb",
    ):
        """
        Handle when a client uploads a certificate file
        """
        return await RESTFilesService.handle_file_upload_multipart_form_part(
            incoming_data, str(Path(NETWORKMANAGER_DIR_FULL, "certs", name)), mode
        )

    @staticmethod
    async def handle_connection_import_file_upload_multipart_form(
        incoming_data: falcon.asgi.multipart.BodyPart, mode: str = "wb"
    ):
        """
        Handle when a client uploads an archive for importing connections
        """
        return await RESTFilesService.handle_file_upload_multipart_form_part(
            incoming_data, CONNECTION_TMP_ARCHIVE_FILE, mode
        )

    @staticmethod
    async def handle_config_import_file_upload_multipart_form(
        incoming_data: falcon.asgi.multipart.BodyPart, mode: str = "wb"
    ):
        """
        Handle when a client uploads an archive for importing system configuration
        """
        return await RESTFilesService.handle_file_upload_multipart_form_part(
            incoming_data, CONFIG_TMP_ARCHIVE_FILE, mode
        )

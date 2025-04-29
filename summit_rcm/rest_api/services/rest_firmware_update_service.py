#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle the firmware update process for the REST API
"""

import os
import falcon.asgi
from summit_rcm.services.firmware_update_service import (
    FirmwareUpdateService,
    NoUpdateInProgressError,
)
from summit_rcm.utils import Singleton, get_running_on_sd
from summit_rcm.services.files_service import FilesService

FILE_STREAMING_BUFFER_SIZE = 128 * 1024
MEDIA_OCTET_STREAM = "application/octet-stream"


class RESTFirmwareUpdateService(FirmwareUpdateService, metaclass=Singleton):
    """Service to handle firmware updates for the REST API"""

    async def handle_update_file_upload_stream(self, stream: falcon.asgi.BoundedStream):
        """Handle an incoming update file stream in chunk sizes of FILE_STREAMING_BUFFER_SIZE"""

        running_on_sd = await get_running_on_sd()

        if self.swclient_fd < 0 and not running_on_sd:
            raise NoUpdateInProgressError("no update in progress")

        if running_on_sd:
            # Get the path to the firmware update file
            fwupdate_file_path = FilesService.get_fwupdate_file_path()

            # If running on SD, we need to create the file if it doesn't exist
            # and remove it if it does exist
            if os.path.isfile(fwupdate_file_path):
                os.remove(fwupdate_file_path)
            else:
                os.mknod(fwupdate_file_path)

            # Create the file and write the data to it
            with open(fwupdate_file_path, "wb") as dest:
                while True:
                    data_chunk = await stream.read(FILE_STREAMING_BUFFER_SIZE)
                    if not data_chunk:
                        return
                    dest.write(data_chunk)
        else:
            # If not running on SD, we need to write the data to the swclient_fd
            while True:
                data_chunk = await stream.read(FILE_STREAMING_BUFFER_SIZE)
                if not data_chunk:
                    return

                self.handle_update_file_chunk(data_chunk)

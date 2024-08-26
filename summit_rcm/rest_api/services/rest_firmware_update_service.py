#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle the firmware update process for the REST API
"""

import falcon.asgi
from summit_rcm.services.firmware_update_service import (
    FirmwareUpdateService,
    NoUpdateInProgressError,
)
from summit_rcm.utils import Singleton

FILE_STREAMING_BUFFER_SIZE = 128 * 1024
MEDIA_OCTET_STREAM = "application/octet-stream"


class RESTFirmwareUpdateService(FirmwareUpdateService, metaclass=Singleton):
    """Service to handle firmware updates for the REST API"""

    async def handle_update_file_upload_stream(self, stream: falcon.asgi.BoundedStream):
        """Handle an incoming update file stream in chunk sizes of FILE_STREAMING_BUFFER_SIZE"""

        if self.swclient_fd < 0:
            raise NoUpdateInProgressError("no update in progress")

        while True:
            data_chunk = await stream.read(FILE_STREAMING_BUFFER_SIZE)
            if not data_chunk:
                return

            self.handle_update_file_chunk(data_chunk)

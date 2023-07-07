"""
Module to handle the firmware update process
"""

import asyncio
from enum import IntEnum, unique
import logging
from subprocess import Popen
from syslog import syslog, LOG_ERR
from typing import Tuple, Optional
import falcon.asgi
import swclient
from summit_rcm.utils import Singleton, get_current_side

FW_UPDATE_SCRIPT = "fw_update"
FILE_STREAMING_BUFFER_SIZE = 128 * 1024
MEDIA_OCTET_STREAM = "application/octet-stream"


@unique
class SummitRCMUpdateStatus(IntEnum):
    """Summit RCM update status enumeration"""

    UPDATED = 0
    """Update completed successfully"""

    FAIL = 1
    """Update failed"""

    NOT_UPDATING = 2
    """No update in process"""

    UPDATING = 5
    """Update in process"""


@unique
class SwupdateStatus(IntEnum):
    """swupdate status enumeration"""

    IDLE = 0
    """Idle"""

    START = 1
    """Start"""

    RUN = 2
    """Run"""

    SUCCESS = 3
    """Success"""

    FAILURE = 4
    """Failure"""

    DOWNLOAD = 5
    """Download"""

    DONE = 6
    """Done"""

    SUBPROCESS = 7
    """Subprocess"""

    BAD_CMD = 8
    """Bad command"""


class FirmwareUpdateService(metaclass=Singleton):
    """Service to handle firmware updates"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.proc: Optional[Popen[str]] = None
        self.status: SummitRCMUpdateStatus = SummitRCMUpdateStatus.NOT_UPDATING
        self.url = ""
        self.image = ""
        self.swclient_fd: int = -1
        self.update_in_progress = False
        self.msg_fd = -1
        self.loop = asyncio.get_event_loop()

    def get_running_mode_for_update(self, image):
        """Retrieve the proper running mode to pass to swupdate based on the kernel command line"""

        try:
            running_mode = image + "-b" if get_current_side() == "a" else image + "-a"
        except Exception as exception:
            syslog(LOG_ERR, str(exception))
            raise exception

        return running_mode

    def get_update_status(self) -> Tuple[int, str]:
        """Retrieve the current update status"""

        try:
            info = ""
            if self.status == SummitRCMUpdateStatus.UPDATED:
                info = "Updated"
            elif self.status == SummitRCMUpdateStatus.FAIL:
                info = "Failed"
            elif self.status == SummitRCMUpdateStatus.NOT_UPDATING:
                info = "No update in progress"
            elif self.status == SummitRCMUpdateStatus.UPDATING:
                info = "Updating..."
            return self.status, info

        except Exception as exception:
            syslog(LOG_ERR, str(exception))
            return SummitRCMUpdateStatus.FAIL, f"Error: {str(exception)}"

    def start_update(self, url: Optional[str], image: Optional[str]):
        """Initiate the firmware update process"""

        if url:
            self.url = url
        if image:
            self.image = image

        if not self.image:
            self.url = ""
            self.image = ""
            raise ValueError("invalid 'image' parameter")

        running_mode = self.get_running_mode_for_update(self.image)

        return_code = self.open_ipc()
        if return_code < 0:
            self.url = ""
            self.image = ""
            raise CouldNotOpenIPCError(
                "Could not open IPC channel with swupdate", return_code
            )

        if self.url:
            # A URL is provided, so pass it and the target 'image' to the fw_update helper script
            # 'close_fds' prevents hang on service stop
            self.proc = Popen(
                [FW_UPDATE_SCRIPT, "-x", "r", "-m", self.image, self.url],
                close_fds=True,
            )
        else:
            # No URL provided, so we expect to be passed the update file in data chunks
            self.swclient_fd = swclient.prepare_fw_update(0, "stable", running_mode)
            if self.swclient_fd <= 0:
                self.url = ""
                self.image = ""
                raise UpdatePreparationError(
                    "error preparing for update", self.swclient_fd
                )
        self.start_progress_monitor(self.swclient_fd)

        # In order to avoid race condition between first update coming from swupdate_client and
        # external REST query, just assume update started unless/until a failure or completion
        # occurs.
        self.status = SummitRCMUpdateStatus.UPDATING

    async def handle_update_file_upload_stream(self, stream: falcon.asgi.BoundedStream):
        """Handle an incoming update file stream in chunk sizes of FILE_STREAMING_BUFFER_SIZE"""

        if self.swclient_fd < 0:
            raise NoUpdateInProgressError("no update in progress")

        while True:
            data_chunk = await stream.read(FILE_STREAMING_BUFFER_SIZE)
            if not data_chunk:
                return

            self.handle_update_file_chunk(data_chunk)

    def handle_update_file_chunk(self, data_chunk: bytes):
        """Handle an incoming update file chunk and pass it to swupdate"""

        if self.swclient_fd < 0:
            raise NoUpdateInProgressError("no update in progress")

        return_code = swclient.do_fw_update(data_chunk, self.swclient_fd)
        if return_code < 0:
            raise UpdateError(return_code, "error during update process")

    def open_ipc(self) -> int:
        """Open the IPC channel with swupdate and return the file descriptor (fd)"""

        if self.msg_fd < 0:
            self.msg_fd = swclient.open_progress_ipc()
            if self.msg_fd < 0:
                syslog(
                    LOG_ERR, "initiate_swupdate: error opening progress IPC connection"
                )
        return self.msg_fd

    def close_ipc(self):
        """Close the previously-opened IPC channel with swupdate"""

        if self.msg_fd >= 0:
            swclient.close_progress_ipc(self.msg_fd)
            self.msg_fd = -1

    def start_progress_monitor(self, swclient_fd: int):
        """Start monitoring the update progress"""

        self.update_in_progress = True
        if self.msg_fd >= 0:
            self.swclient_fd = swclient_fd
            self.loop.add_reader(self.msg_fd, self.progress_event_handler)

    def stop_progress_monitor(self):
        """Stop monitoring the update progress"""

        self.update_in_progress = False
        swclient.end_fw_update(self.swclient_fd)
        self.loop.remove_reader(self.msg_fd)
        self.close_ipc()
        self.swclient_fd = -1
        self.url = ""
        self.image = ""

    def progress_event_handler(self):
        """Handle a swupdate progress event"""

        if not self.update_in_progress:
            return

        try:
            # Read data - progress message format is:
            # - status
            # - nsteps
            # - cur_step
            # - cur_percent
            # - cur_image
            # - info
            status, _, _, _, _, _ = swclient.read_progress_ipc(self.msg_fd)

            if status is None:
                return

            if status in [SwupdateStatus.SUCCESS, SwupdateStatus.FAILURE]:
                # See swupdate-progress.c
                # Latch success & failure messages, ignoring all others.
                if status == SwupdateStatus.SUCCESS:
                    self.status = SummitRCMUpdateStatus.UPDATED
                elif status == SwupdateStatus.FAILURE:
                    self.status = SummitRCMUpdateStatus.FAIL

                # Close down the progress monitor after completion
                self.stop_progress_monitor()
        except Exception as exception:
            syslog(LOG_ERR, f"Failed reading progress update: {str(exception)}")

    def cancel_update(self):
        """Cancel an in-progress update"""
        self.stop_progress_monitor()
        self.status = SummitRCMUpdateStatus.NOT_UPDATING


class NoUpdateInProgressError(Exception):
    """
    Custom error for when an update file is uploaded before the update process has properly been
    initiated.
    """


class UpdateError(Exception):
    """
    Custom error for when an error occurs during the update process.
    """

    def __init__(self, return_code: int, *args: object) -> None:
        super().__init__(*args)
        self.return_code = return_code


class CouldNotOpenIPCError(Exception):
    """
    Custom error for when an error occurs opening the IPC channel to swupdate.
    """

    def __init__(self, return_code: int, *args: object) -> None:
        super().__init__(*args)
        self.return_code = return_code


class UpdatePreparationError(Exception):
    """
    Custom error for when an error occurs preparing for the swupdate process.
    """

    def __init__(self, swclient_fd: int, *args: object) -> None:
        super().__init__(*args)
        self.return_code = swclient_fd

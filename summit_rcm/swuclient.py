import select
import threading
from syslog import LOG_ERR, syslog
from typing import Optional

import swclient

SWU_STATUS_IDLE = 0
SWU_STATUS_START = 1
SWU_STATUS_RUN = 2
SWU_STATUS_SUCCESS = 3
SWU_STATUS_FAILURE = 4
SWU_STATUS_DOWNLOAD = 5
SWU_STATUS_DONE = 6
SWU_STATUS_SUBPROCESS = 7
SWU_STATUS_BAD_CMD = 8

SWUPDATE_POLL_TIMEOUT = 0.2


class SWUpdateClient:
    def __init__(self, handler):
        self.recv_handler = handler
        self.proc = None
        self.update_in_progress = False
        self.state = None
        self.msg_fd = -1
        self.progress_thread: Optional[threading.Thread] = None

    def open_ipc(self) -> int:
        if self.msg_fd < 0:
            self.msg_fd = swclient.open_progress_ipc()
            if self.msg_fd < 0:
                syslog(
                    LOG_ERR, "initiate_swupdate: error opening progress IPC connection"
                )
        return self.msg_fd

    def close_ipc(self):
        if self.msg_fd >= 0:
            swclient.close_progress_ipc(self.msg_fd)
            self.msg_fd = -1

    def start_progress_thread(self, swclient_fd: int):
        self.update_in_progress = True
        self.progress_thread = threading.Thread(
            target=self.monitor_update_progress, args=(swclient_fd,), daemon=True
        )
        self.progress_thread.start()

    def stop_progress_thread(self):
        self.update_in_progress = False

    def join_progress_thread(self):
        self.update_in_progress = False
        if self.progress_thread:
            self.progress_thread.join()
            self.progress_thread = None

    def monitor_update_progress(self, swclient_fd: int):
        try:
            poller = select.poll()
            poller.register(self.msg_fd, select.POLLIN)

            # Only monitor the progress socket while an update is in progress
            while self.update_in_progress:
                events = poller.poll(SWUPDATE_POLL_TIMEOUT)
                for descriptor, event in events:
                    if descriptor == self.msg_fd and event is select.POLLIN:
                        # Read data
                        fw_update_state = swclient.read_progress_ipc(self.msg_fd)
                        if fw_update_state == None:
                            continue

                        self.progress_handler(
                            fw_update_state[0],  # status
                            fw_update_state[4],  # cur_image
                            fw_update_state[5],  # info
                        )

        except Exception as e:
            syslog(LOG_ERR, "Failed reading progress update: '%s'" % str(e))

        finally:
            # Cleanup
            if poller and self.msg_fd >= 0:
                poller.unregister(self.msg_fd)
            if swclient_fd >= 0:
                swclient.end_fw_update(swclient_fd)
            self.close_ipc()
            self.update_in_progress = False

    def progress_handler(self, status, curr_image, msg):
        self.state = status
        if curr_image:
            rcurr_img = curr_image.strip("\x00")
        else:
            rcurr_img = None
        self.recv_handler(status, rcurr_img, msg)

    def get_state(self):
        return self.state

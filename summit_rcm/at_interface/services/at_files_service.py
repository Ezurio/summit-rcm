"""
Module to handle receiving files serially through the AT Interface
"""
import time
from syslog import LOG_ERR, syslog
from typing import Tuple
from summit_rcm.utils import Singleton
import summit_rcm.at_interface.fsm as fsm


class ATFilesService(object, metaclass=Singleton):
    """Service to handle serial data mode for files sent through the AT Interface"""

    escape_delay: float = 0.2
    escape_count: int = 0
    escape: bool = False
    rx_timestamp: float = 0.0

    def __init__(self) -> None:
        self.data_buffer = b""
        self.busy = False
        self.listener_id = -1

    async def write_upload_body(
        self, length: int, buffer_size: int = 0
    ) -> Tuple[bool, bytes, int]:
        """
        Handle constructing payload of a file upload
        """
        state_machine = fsm.ATInterfaceFSM()
        if self.escape:
            self.escape = False
            self.busy = False
            self.data_buffer = b""
            state_machine.deregister_listener(self.listener_id)
            return (True, "", -1)
        if len(self.data_buffer) >= length:
            syslog(LOG_ERR, f"Total Length size({length} met, returning body to command)")
            self.data_buffer = self.data_buffer[:length]
            state_machine.deregister_listener(self.listener_id)
            body = self.data_buffer
            self.busy = False
            self.data_buffer = b""
            return (True, body, length)
        if len(self.data_buffer) >= buffer_size and buffer_size:
            syslog(LOG_ERR, f"Buffer size({buffer_size} met, returning body to command)")
            body = self.data_buffer[:buffer_size]
            self.data_buffer = self.data_buffer[buffer_size:]
            syslog(LOG_ERR, f"Length of body is {len(body)}")
            return (True, body, len(body))

        def data_received(data: bytes):
            self.data_buffer += data
            try:
                decoded_buffer = self.data_buffer[-3:].decode("utf-8")
            except Exception:
                decoded_buffer = ""
            dec_length = len(decoded_buffer)
            less_than_delay = (
                True
                if (time.time() - self.rx_timestamp) <= self.escape_delay
                else False
            )
            if not (dec_length > 0 and decoded_buffer[-1] == "+"):
                self.escape_count = 0
            elif less_than_delay and self.escape_count != 0:
                self.escape_count += 1
                if self.escape_count == 3:
                    self.escape_count = 0
                    self.escape = True
            elif not less_than_delay:
                self.escape_count = 1
            self.rx_timestamp = time.time()

        if not self.busy:
            self.busy = True
            self.listener_id = state_machine.register_listener(data_received)

        return (False, "", 0)

    def transfer_in_process(self) -> bool:
        """Returns whether or not a transfer is in process"""
        return self.busy

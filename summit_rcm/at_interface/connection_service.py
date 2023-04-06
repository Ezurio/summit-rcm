import asyncio
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass
from summit_rcm.at_interface.dialer import Dialer

from summit_rcm.utils import Singleton
import summit_rcm.at_interface.fsm as fsm


@dataclass
class Connection:
    id: int
    type: str
    addr: str
    port: int
    keepalive: int
    connected: bool
    dialer: Dialer
    data_buffer: bytes
    listener_id: int
    busy: bool

    def on_connection_made(self):
        fsm.ATInterfaceFSM().dte_output(f"+IP, {self.id} Connected\r\n")

    def on_data_received(self, data: bytes):
        fsm.ATInterfaceFSM().dte_output(
            f"+IPD: {self.id},{str(data.decode('utf-8'))}\r\n"
        )

    def on_connection_lost(self):
        fsm.ATInterfaceFSM().dte_output(f"+IP, {self.id} Disconnected\r\n")
        if ConnectionService().connections[self.id].connected:
            ConnectionService().close_connection(self.id)


class ConnectionService(object, metaclass=Singleton):
    MAX_CONNECTIONS = 6
    escape_delay = 0.02
    escape_count = 0
    escape = False
    rx_timestamp = 0

    def __init__(self) -> None:
        # Pre-populate connection list
        self.connections: List[Connection] = []
        for i in range(self.MAX_CONNECTIONS):
            current_connection = Connection(
                id=i,
                type="",
                addr="",
                port=0,
                connected=False,
                keepalive=0,
                dialer=Dialer(asyncio.get_event_loop()),
                data_buffer=bytes("", "utf-8"),
                listener_id=-1,
                busy=False,
            )
            current_connection.dialer.on_connection_made = (
                current_connection.on_connection_made
            )
            current_connection.dialer.on_data_received = (
                current_connection.on_data_received
            )
            current_connection.dialer.on_connection_lost = (
                current_connection.on_connection_lost
            )
            self.connections.append(current_connection)

    @staticmethod
    def validate_connection_type(input: str) -> bool:
        """
        Analyzes the input string and returns the True if the connection type value is valid.
        Otherwise, return False.
        """
        if input == "tcp" or input == "udp" or input == "ssl":
            return True
        else:
            return False

    def start_connection(
        self,
        id: int,
        type: str,
        addr: str,
        port: int,
        keepalive: int,
    ) -> bool:
        """
        Start a new IP connection and return success/failure
        """
        if id < 0 or id > self.MAX_CONNECTIONS - 1:
            # Invalid index
            return False

        if self.connections[id].connected:
            # Already connected
            return False

        self.connections[id].type = type
        self.connections[id].addr = addr
        self.connections[id].port = port
        self.connections[id].keepalive = keepalive

        try:
            self.connections[id].dialer.dial(
                f"{self.connections[id].addr}:{self.connections[id].port}",
                keepalive,
                type,
            )
            self.connections[id].connected = True
        except Exception:
            self.connections[id].connected = False
            return False
        return True

    def close_connection(self, id: int) -> bool:
        """
        Close an existing IP connection and return success/failure
        """
        if id < 0 or id > self.MAX_CONNECTIONS - 1:
            # Invalid index
            return False

        if not self.connections[id].connected:
            # Already closed
            return False

        try:
            self.connections[id].dialer.hangup()
            self.connections[id].connected = False
            self.connections[id].addr = ""
            self.connections[id].port = 0
            self.connections[id].type = ""
            self.connections[id].keepalive = 0
            self.connections[id].data_buffer = b""
            self.connections[id].listener_id = -1
            self.connections[id].busy = False
        except Exception:
            return False
        return True

    def send_data(self, id: int, length: bytes) -> Tuple[bool, int]:
        """
        Send data to an existing IP connection and return success/failure
        """
        if id < 0 or id > self.MAX_CONNECTIONS - 1:
            # Invalid index
            return (True, 0)

        connection = self.connections[id]
        state_machine = fsm.ATInterfaceFSM()

        if not connection.connected:
            # Not connected
            return (True, 0)

        if self.escape:
            self.escape = False
            connection.busy = False
            connection.data_buffer = b""
            state_machine.deregister_listener(connection.listener_id)
            return (True, -1)

        if len(connection.data_buffer) >= length:
            connection.data_buffer = connection.data_buffer[:length]
            state_machine.deregister_listener(connection.listener_id)

            try:
                connection.dialer.write(connection.data_buffer)
            except Exception:
                connection.busy = False
                return (True, 0)
            connection.busy = False
            connection.data_buffer = b""
            return (True, length)

        def data_received(data: bytes):
            nonlocal connection
            connection.data_buffer += data
            decoded_buffer = connection.data_buffer.decode("utf-8")
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

        if not connection.busy:
            connection.busy = True
            connection.listener_id = state_machine.register_listener(data_received)

        return (False, 0)

    def is_connection_busy(self, id: int) -> Optional[bool]:
        """
        Returns whether or not the target connection is busy or None if the given id is invalid.
        """
        if (
            id < 0
            or id > self.MAX_CONNECTIONS - 1
            or not self.connections[id].connected
        ):
            # Invalid index
            return None

        return self.connections[id].busy

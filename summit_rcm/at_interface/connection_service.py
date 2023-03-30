import asyncio
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum, unique
from summit_rcm.at_interface.tcpdialler import TcpDialler

from summit_rcm.utils import Singleton
import summit_rcm.at_interface.fsm as fsm


@unique
class ConnectionType(IntEnum):
    TCP = 0
    """TCP connection"""

    UDP = 1
    """UDP connection"""

    SSL = 2
    """SSL connection"""


@dataclass
class Connection:
    id: int
    type: ConnectionType
    addr: str
    port: int
    enable_keepalive: bool
    connected: bool
    dialer: TcpDialler
    data_buffer: bytes
    listener_id: int
    busy: bool

    def on_connection_made(self):
        fsm.ATInterfaceFSM().dte_output(
            f"+IP, {self.id} Connected\r\n"
        )

    def on_data_received(self, data: bytes):
        fsm.ATInterfaceFSM().dte_output(
            f"+IPD: {self.id},{str(data.decode('utf-8'))}\r\n"
        )

    def on_connection_lost(self):
        fsm.ATInterfaceFSM().dte_output(
            f"+IP, {self.id} Disconnected\r\n"
        )


class ConnectionService(object, metaclass=Singleton):
    MAX_CONNECTIONS = 6

    def __init__(self) -> None:
        # Pre-populate connection list
        self.connections: List[Connection] = []
        for i in range(self.MAX_CONNECTIONS):
            current_connection = Connection(
                id=i,
                type=ConnectionType.TCP,
                addr="",
                port=0,
                connected=False,
                enable_keepalive=False,
                dialer=TcpDialler(asyncio.get_event_loop()),
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
    def parse_connection_type(input: str) -> Optional[ConnectionType]:
        """
        Parse the input string and return the appropriate connection type value, if valid.
        Otherwise, return None.
        """
        input = input.lower()

        if input == "tcp":
            return ConnectionType.TCP
        elif input == "udp":
            return ConnectionType.UDP
        elif input == "ssl":
            return ConnectionType.SSL
        else:
            return None

    def start_connection(
        self,
        id: int,
        type: ConnectionType,
        addr: str,
        port: int,
        enable_keepalve: bool = False,
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
        self.connections[id].enable_keepalve = enable_keepalve

        try:
            self.connections[id].dialer.dial(
                f"{self.connections[id].addr}:{self.connections[id].port}"
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
            self.connections[id].type = ConnectionType.TCP
            self.connections[id].enable_keepalive = False
            self.connections[id].data_buffer = bytes("", "utf-8")
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

        if len(connection.data_buffer) >= length:
            connection.data_buffer = connection.data_buffer[:length]
            state_machine.deregister_listener(connection.listener_id)

            try:
                connection.dialer.write(connection.data_buffer)
            except Exception:
                connection.busy = False
                return (True, 0)
            connection.busy = False
            return (True, length)

        def data_received(data: bytes):
            nonlocal connection
            connection.data_buffer += data

        if not connection.busy:
            connection.busy = True
            connection.listener_id = state_machine.register_listener(data_received)

        return (False, 0)

    def is_connection_busy(self, id: int) -> Optional[bool]:
        """
        Returns whether or not the target connection is busy or None if the given id is invalid.
        """
        if id < 0 or id > self.MAX_CONNECTIONS - 1:
            # Invalid index
            return None

        return self.connections[id].busy

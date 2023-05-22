"""
Module to handle IP Connections
"""
import asyncio
from syslog import syslog, LOG_ERR
import time
from typing import List, Optional, Tuple
import ssl as SSL
from summit_rcm.at_interface.services.dialer_service import Dialer

from summit_rcm.utils import Singleton
import summit_rcm.at_interface.fsm as fsm
from summit_rcm.definition import SSLModes


class Connection:
    """
    Defines an IP Connection
    """

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

    def __init__(
        self,
        id: int,
        type: str,
        addr: str,
        port: int,
        keepalive: int,
        connected: bool,
        dialer: Dialer,
        data_buffer: bytes,
        listener_id: int,
        busy: bool,
        ssl_context: SSL.SSLContext = None,
    ) -> None:
        self.id = id
        self.type = type
        self.addr = addr
        self.port = port
        self.keepalive = keepalive
        self.connected = connected
        self.dialer = dialer
        self.data_buffer = data_buffer
        self.listener_id = listener_id
        self.busy = busy
        self.ssl_context = ssl_context

    def on_connection_made(self):
        fsm.ATInterfaceFSM().at_output(
            f"+IP: {self.id},Connected", print_trailing_line_break=False
        )

    def on_data_received(self, data: bytes):
        fsm.ATInterfaceFSM().at_output(
            f"+IPD: {self.id},{len(data)},".encode("utf-8") + data,
            print_leading_line_break=False,
        )

    def on_datagram_received(self, data: bytes, addr: Tuple[str, int]):
        fsm.ATInterfaceFSM().at_output(
            f"+IPD: {self.id},{len(data)},'{addr[0]}',{addr[1]},".encode("utf-8")
            + data,
            print_leading_line_break=False,
        )

    def on_connection_lost(self):
        fsm.ATInterfaceFSM().at_output(
            f"+IP: {self.id},Disconnected", print_leading_line_break=False
        )
        if ConnectionService().connections[self.id].connected:
            ConnectionService().close_connection(self.id)


class ConnectionService(object, metaclass=Singleton):
    """
    Service class to handle IP Connections
    """

    MAX_CONNECTIONS: int = 6
    escape_delay: float = 0.02
    escape_count: int = 0
    escape: bool = False
    rx_timestamp: float = 0.0

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
                ssl_context=None,
            )
            current_connection.dialer.on_connection_made = (
                current_connection.on_connection_made
            )
            current_connection.dialer.on_data_received = (
                current_connection.on_data_received
            )
            current_connection.dialer.on_datagram_received = (
                current_connection.on_datagram_received
            )
            current_connection.dialer.on_connection_lost = (
                current_connection.on_connection_lost
            )
            self.connections.append(current_connection)

    async def start_connection(
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
            await self.connections[id].dialer.dial(
                f"{self.connections[id].addr}:{self.connections[id].port}",
                keepalive,
                type,
                self.connections[id].ssl_context,
            )
            self.connections[id].connected = True
        except Exception as e:
            self.connections[id].connected = False
            syslog(LOG_ERR, f"Error starting connection: {str(e)}")
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
        except Exception:
            pass
        self.connections[id].connected = False
        self.connections[id].addr = ""
        self.connections[id].port = 0
        self.connections[id].type = ""
        self.connections[id].keepalive = 0
        self.connections[id].data_buffer = b""
        self.connections[id].listener_id = -1
        self.connections[id].busy = False
        self.connections[id].ssl_context = None
        return True

    def send_data(self, id: int, length: int) -> Tuple[bool, int]:
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

    def configure_cip_ssl(
        self,
        id: int,
        auth_mode: int,
        check_hostname: bool,
        key: str,
        cert: str,
        ca: str,
    ):
        """
        Changes status of SSL to disabled, enabled without host verification, or
        enabled with host verification and produces ssl context
        """
        try:
            context = SSL.SSLContext(SSL.PROTOCOL_TLS_CLIENT)
            context.check_hostname = check_hostname
            ssl = SSLModes(auth_mode)
            if ssl == SSLModes.NO_AUTH:
                context.verify_mode = SSL.CERT_NONE
            elif ssl == SSLModes.CLIENT_VERIFY_SERVER:
                context.load_default_certs()
                context.load_verify_locations(cafile=ca)
            elif ssl == SSLModes.SERVER_VERIFY_CLIENT:
                context.verify_mode = SSL.CERT_NONE
                context.load_cert_chain(cert, key)
            else:
                context.load_default_certs()
                context.load_verify_locations(cafile=ca)
                context.load_cert_chain(cert, key)
            self.connections[id].ssl_context = context
            return
        except Exception as exception:
            self.connections[id].ssl_context = None
            raise exception

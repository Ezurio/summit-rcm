"""
Module to handle AT Interface Socket Implementation
"""
import asyncio
import asyncio.transports
import socket
import ssl
from typing import Tuple

from typing import Optional


class StreamingProtocol(asyncio.Protocol):
    """Transport Protocol for a TCP or SSL socket"""
    def __init__(self, dialer):
        self.dialer = dialer
        self.dialer.protocol = self

    def connection_made(self, transport: asyncio.transports.BaseTransport):
        self.transport = transport
        if self.dialer.on_connection_made:
            self.dialer.on_connection_made()

    def data_received(self, data: bytes):
        if self.dialer.on_data_received:
            self.dialer.on_data_received(data)

    def connection_lost(self, exc: Optional[Exception]):
        self.dialer.protocol = None
        if self.dialer.on_connection_lost:
            self.dialer.on_connection_lost()


class UserDatagramProtocol(asyncio.DatagramProtocol):
    """Transport Protocol for a UDP socket"""
    def __init__(self, dialer):
        self.dialer = dialer
        self.dialer.protocol = self

    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport
        if self.dialer.on_connection_made:
            self.dialer.on_connection_made()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        if self.dialer.on_datagram_received:
            self.dialer.on_datagram_received(data, addr)

    def connection_lost(self, exc: Optional[Exception]):
        self.dialer.protocol = None
        if self.dialer.on_connection_lost:
            self.dialer.on_connection_lost()


class Dialer:
    """Dialer class to handle creation of transports and protocols for AT Interface Sockets"""
    def __init__(self, loop):
        self.loop = loop
        self.protocol = None
        self.on_connection_made = None
        self.on_data_received = None
        self.on_datagram_received = None
        self.on_connection_lost = None

    def dial(self, number: str, keepalive: int, type: str):
        """Create Socket"""
        (host, port) = number.split(":")
        if type == "udp":
            c = self.loop.create_datagram_endpoint(
                lambda: create_protocol(self, type), remote_addr=(host, port)
            )
            self.loop.create_task(c)
            return (None, "", "")
        elif type == "tcp":
            socks = setup_tcp_socket(host, port, keepalive)
        else:
            (socks, context) = setup_ssl_socket(host, port, keepalive)
        c = self.loop.create_connection(
            lambda: create_protocol(self, type),
            server_hostname=host if type == "ssl" else None,
            sock=socks,
            ssl=context if type == "ssl" else None,
        )
        self.loop.create_task(c)
        return (None, "", "")

    def hangup(self):
        """Hangup socket"""
        if self.protocol and self.protocol.transport:
            self.protocol.transport.abort()

    def write(self, s):
        """Write to socket"""
        if isinstance(self.protocol, StreamingProtocol) and self.protocol.transport:
            self.protocol.transport.write(s)
        else:
            self.protocol.transport.sendto(s)


def create_protocol(dialer, type: str) -> asyncio.BaseProtocol | None:
    """Create socket protocol"""
    if type == "tcp" or type == "ssl":
        return StreamingProtocol(dialer)
    elif type == "udp":
        return UserDatagramProtocol(dialer)
    else:
        return None


def setup_tcp_socket(host: str, port: str, keepalive: int) -> socket:
    """Set up TCP Socket"""
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.connect((host, int(port)))
    if keepalive != 0:
        setup_keepalive(socks, keepalive)
    return socks


def setup_ssl_socket(host: str, port: str, keepalive: int):
    """Set up SSL socket"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.connect((host, int(port)))
    if keepalive != 0:
        setup_keepalive(socks, keepalive)
    return (socks, context)


def setup_keepalive(sock: socket, keepalive: int):
    """Set up socket keepalive"""
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, keepalive)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

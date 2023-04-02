import asyncio
import asyncio.transports
import socket

from typing import Optional


class TcpDiallerProtocol(asyncio.Protocol):
    def __init__(self, dialler):
        self.dialler = dialler
        self.dialler.protocol = self

    def connection_made(self, transport: asyncio.transports.BaseTransport):
        self.transport = transport
        if self.dialler.on_connection_made:
            self.dialler.on_connection_made()

    def data_received(self, data: bytes):
        if self.dialler.on_data_received:
            self.dialler.on_data_received(data)

    def connection_lost(self, exc: Optional[Exception]):
        self.dialler.protocol = None
        if self.dialler.on_connection_lost:
            self.dialler.on_connection_lost()


class TcpDialler:
    def __init__(self, loop):
        self.loop = loop
        self.protocol = None
        self.on_connection_made = None
        self.on_data_received = None
        self.on_connection_lost = None

    def dial(self, number: str, keepalive: int):
        (host, port) = number.split(":")
        socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socks.connect((host, int(port)))
        if keepalive != 0:
            socks.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            socks.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, keepalive)
            socks.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
            socks.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        c = self.loop.create_connection(lambda: TcpDiallerProtocol(self), sock=socks)
        self.loop.create_task(c)
        return (None, "", "")

    def hangup(self):
        if self.protocol and self.protocol.transport:
            self.protocol.transport.abort()

    def write(self, s):
        if self.protocol and self.protocol.transport:
            self.protocol.transport.write(s)

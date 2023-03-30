import asyncio
import asyncio.transports


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

    def dial(self, number):
        (host, port) = number.split(":")
        c = self.loop.create_connection(
            lambda: TcpDiallerProtocol(self), host, int(port)
        )
        self.loop.create_task(c)
        return (None, "", "")

    def hangup(self):
        if self.protocol and self.protocol.transport:
            self.protocol.transport.abort()

    def write(self, s):
        if self.protocol and self.protocol.transport:
            self.protocol.transport.write(s)

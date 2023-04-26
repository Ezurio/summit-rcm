import asyncio
from summit_rcm.at_interface.fsm import ATInterfaceFSM
import serial_asyncio


class ATInterfaceSerialProtocol(asyncio.Protocol):
    def connection_made(self, transport) -> None:
        self.transport = transport

    def data_received(self, data) -> None:
        asyncio.ensure_future(ATInterfaceFSM().on_input_received(data))

    def connection_lost(self, exc) -> None:
        pass


class ATInterface:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop: asyncio.AbstractEventLoop = loop

    async def start(self):
        transport, protocol = await serial_asyncio.create_serial_connection(
            self.loop, ATInterfaceSerialProtocol, "/dev/ttyS2", baudrate=115200
        )
        ATInterfaceFSM()._transport = transport
        ATInterfaceFSM()._protocol = protocol
        self.loop.call_later(0.1, self.repeat)

    def repeat(self):
        ATInterfaceFSM().check_escape()
        self.loop.call_later(0.1, self.repeat)
        if ATInterfaceFSM().quit:
            self.loop.stop()

import asyncio
from syslog import LOG_ERR, syslog
import threading
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
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def start(self):
        coro = serial_asyncio.create_serial_connection(
            self.loop, ATInterfaceSerialProtocol, "/dev/ttyS2", baudrate=115200
        )
        transport, protocol = self.loop.run_until_complete(coro)
        ATInterfaceFSM()._transport = transport
        ATInterfaceFSM()._protocol = protocol
        self.loop.call_later(0.1, self.repeat)
        try:
            threading.Thread(target=self.loop.run_forever, daemon=True).start()
        except Exception as e:
            syslog(LOG_ERR, f"ATInterface error: {str(e)}")

    def repeat(self):
        ATInterfaceFSM().check_escape()
        self.loop.call_later(0.1, self.repeat)
        if ATInterfaceFSM().quit:
            self.loop.stop()

import asyncio
import serial_asyncio
from syslog import LOG_ERR, syslog
from summit_rcm.settings import ServerConfig
from summit_rcm.at_interface.fsm import ATInterfaceFSM


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
        serial_port = (
            ServerConfig()
            .get_parser()
            .get("summit-rcm", "serial_port", fallback=None)
            .strip('"')
        )
        baud_rate = (
            ServerConfig().get_parser().getint("summit-rcm", "baud_rate", fallback=None)
        )
        if serial_port is None or baud_rate is None:
            syslog(LOG_ERR, "AT Interface Failed: Invalid/Unspecified Serial Port Configuration")
            raise ValueError("AT Interface Failed: Invalid/Unspecified Serial Port Configuration")
        transport, protocol = await serial_asyncio.create_serial_connection(
            self.loop,
            ATInterfaceSerialProtocol,
            serial_port,
            baud_rate,
        )
        ATInterfaceFSM()._transport = transport
        ATInterfaceFSM()._protocol = protocol
        self.loop.call_later(0.1, self.repeat)

    def repeat(self):
        ATInterfaceFSM().check_escape()
        self.loop.call_later(0.1, self.repeat)
        if ATInterfaceFSM().quit:
            self.loop.stop()

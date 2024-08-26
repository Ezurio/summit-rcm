#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Main AT Interface Module
"""

from syslog import LOG_ERR, syslog
import asyncio
import signal
import serial_asyncio
from summit_rcm.at_interface.fsm import ATInterfaceFSM
from summit_rcm.services.date_time_service import DateTimeService
from summit_rcm.settings import ServerConfig


class ATInterfaceSerialProtocol(asyncio.Protocol):
    """The AT Interface's Asyncio Protocol"""

    def connection_made(self, transport) -> None:
        self.transport = transport

    def data_received(self, data) -> None:
        asyncio.ensure_future(ATInterfaceFSM().on_input_received(data))

    def connection_lost(self, exc) -> None:
        pass


class ATInterface:
    """Class that establishes the AT Interface"""

    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.stop_requested: bool = False
        self.state_machine: ATInterfaceFSM = ATInterfaceFSM()

    def signal_handler(self, _signal, _frame):
        """Handles the signals"""
        self.stop_requested = True
        if self.state_machine._transport is not None:
            self.state_machine._transport.close()

    async def start(self):
        """Starts the AT Interface"""
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
            syslog(
                LOG_ERR,
                "AT Interface Failed: Invalid/Unspecified Serial Port Configuration",
            )
            raise ValueError(
                "AT Interface Failed: Invalid/Unspecified Serial Port Configuration"
            )
        transport, protocol = await serial_asyncio.create_serial_connection(
            self.loop,
            ATInterfaceSerialProtocol,
            serial_port,
            baud_rate,
            rtscts=True,
        )
        self.state_machine._transport = transport
        self.state_machine._protocol = protocol
        await DateTimeService().populate_time_zone_list()

        # Configure signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.state_machine.at_output("READY")

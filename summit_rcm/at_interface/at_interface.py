#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Main AT Interface Module
"""

import termios
import os
import fcntl
import struct
from syslog import LOG_ERR, syslog
import asyncio
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

    def close(self) -> None:
        """Closes the AT Interface"""
        self.stop_requested = True
        self.state_machine.close()

    def _set_closing_wait(
        self, serial_port: str = None, closing_wait_in: int = 65535
    ) -> None:
        """
        Sets the closing wait time for the serial port

        See include/uapi/linux/serial.h from the Linux kernel for the definition of serial_struct.

        :param serial_port: The serial port to configure
        :param closing_wait_in: The closing wait time in centiseconds with special handling for 0
         (wait forever) and 65535 (disable wait)
        """
        if not serial_port:
            raise ValueError("AT Interface Failed: Invalid Serial Port")

        if closing_wait_in < 0 or closing_wait_in > 65535:
            raise ValueError("AT Interface Failed: Invalid Closing Wait Time")

        fmt = "iiIiiiiiHcsiHHPHHL"

        try:
            # Open the serial port
            fd = os.open(serial_port, os.O_RDWR | os.O_NOCTTY)

            # Get the current serial port settings
            serial_info = bytearray(struct.calcsize(fmt))
            fcntl.ioctl(fd, termios.TIOCGSERIAL, serial_info)
            (
                type,
                line,
                port,
                irq,
                flags,
                xmit_fifo_size,
                custom_divisor,
                baud_base,
                close_delay,
                io_type,
                reserved_char_bytes,
                hub6,
                closing_wait,
                closing_wait2,
                iomem_base,
                iomem_reg_shift,
                port_high,
                iomap_base,
            ) = struct.unpack(fmt, serial_info)

            # Set the closing wait time
            closing_wait = closing_wait_in

            # Set the new serial port settings using TIOCSSERIAL
            serial_info = struct.pack(
                fmt,
                type,
                line,
                port,
                irq,
                flags,
                xmit_fifo_size,
                custom_divisor,
                baud_base,
                close_delay,
                io_type,
                reserved_char_bytes,
                hub6,
                closing_wait,
                closing_wait2,
                iomem_base,
                iomem_reg_shift,
                port_high,
                iomap_base,
            )
            fcntl.ioctl(fd, termios.TIOCSSERIAL, serial_info)

        finally:
            # Close the serial port
            os.close(fd)

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

        self._set_closing_wait(serial_port=serial_port, closing_wait_in=65535)

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

        self.state_machine.at_output("READY")

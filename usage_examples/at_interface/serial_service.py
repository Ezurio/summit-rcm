"""
Module to handle AT Interface Command Execution
"""
import asyncio
from re import search
from typing import Tuple, Optional
import serial_asyncio
import aiofiles


REBOOT_COMMANDS = [
    "AT+POWER=3\r",
    "AT+FACTRESET=1\r",
    "AT+FIPS=0,1\r",
    "AT+FIPS=1,1\r",
    "AT+FIPS=2,1\r",
]


class ATInterfaceSerialProtocol(asyncio.Protocol):
    """
    Class that defines the AT interface serial protocol
    """
    carrot_received = False
    ok_received = False
    error_received = False
    ready_received = True
    data_buffer = b""
    registered_handlers = {}

    def register_handler(self, URC, handler):
        """
        Function to handle asynchronous messaging
        """
        self.registered_handlers[URC] = handler

    def connection_made(self, transport) -> None:
        self.transport = transport

    def data_received(self, data) -> None:
        try:
            try:
                data_list = data.decode("utf-8").split("\r\n")
                for i, data_str in enumerate(data_list):
                    handler_found = False
                    for URC, handler in self.registered_handlers.items():
                        if data_str.startswith(URC):
                            handler(data_str)
                            handler_found = True
                            break
                    if not handler_found:
                        self.data_buffer += data_str.encode("utf-8")
                        if i < (len(data_list) - 1):
                            self.data_buffer += "\r\n".encode("utf-8")
            except UnicodeDecodeError:
                self.data_buffer += data

            if not self.carrot_received:
                self.carrot_received = "\r\n> " in self.data_buffer[-4:].decode("utf-8")
            if not self.ok_received:
                self.ok_received = "\r\nOK\r\n" in self.data_buffer[-6:].decode("utf-8")
            if not self.error_received:
                self.error_received = "\r\nERROR\r\n" in self.data_buffer[-9:].decode(
                    "utf-8"
                )
                if self.error_received:
                    self.data_buffer = self.data_buffer[:-9]
            if not self.ready_received:
                self.ready_received = "\r\nREADY\r\n" in self.data_buffer[-9:].decode(
                    "utf-8"
                )
                if self.ready_received:
                    self.data_buffer = self.data_buffer[:-9]
        except Exception:
            pass

    def connection_lost(self, exc) -> None:
        pass

    def pause_writing(self):
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())


class ATSession(object):
    """
    Class that defines an AT session instance and handles executing AT commands
    """
    def __init__(self, serial_port: str, baud_rate: int):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.validate_response = True

    async def execute_command(
        self,
        command: str,
        expected_response: str,
        delay: int = 0,
        doppelganger: Optional[Tuple] = (),
    ) -> str | bytes:
        """
        Write a command to the serial port and return the AT Interface response
        """
        self.protocol.carrot_received = False
        self.protocol.ok_received = False
        while not self.protocol.ready_received:
            await asyncio.sleep(1)
        if delay:
            await asyncio.sleep(delay)
        self.transport.write(command.encode())

        if command in REBOOT_COMMANDS:
            self.protocol.ready_received = False

        while (
            not self.protocol.ok_received
            and not self.protocol.error_received
            and not self.protocol.carrot_received
        ):
            await asyncio.sleep(0.1)

        if self.protocol.error_received:
            if doppelganger:
                self.protocol.error_received = False
                print(f"\r\nERROR\r\n{doppelganger[0]}", end="")
                self.protocol.data_buffer = await self.execute_command(*doppelganger)
                self.validate_response = False
            else:
                raise ATErrorException("ERROR Received")

        try:
            data = self.protocol.data_buffer.decode("utf-8")
            validate_response = data
        except UnicodeDecodeError:
            data = self.protocol.data_buffer
            validate_response = data.decode("utf-8", "ignore")
        except AttributeError:
            data = self.protocol.data_buffer
            validate_response = data
        if search(expected_response, validate_response) is None and self.validate_response:
            raise ATUnexpectedResponseException(f"Received Unexpected Response: {data}")
        self.protocol.data_buffer = b""
        self.validate_response = True
        return data

    async def send_file(self, file: str):
        """
        Send a file through the serial port
        """
        async with aiofiles.open(file, "rb") as temp_file:
            while True:
                data = await temp_file.read(1024 * 64)
                if not data:
                    break
                self.transport.write(data)
                while self.transport.get_write_buffer_size() > (1024 * 60):
                    await asyncio.sleep(0.05)
        await asyncio.sleep(5)
        try:
            data = self.protocol.data_buffer.decode("utf-8")
        except Exception:
            data = self.protocol.data_buffer
        return data

    async def open_serial(self):
        """
        Opens the serial port
        """
        self.transport, self.protocol = await serial_asyncio.create_serial_connection(
            asyncio.get_event_loop(),
            ATInterfaceSerialProtocol,
            self.serial_port,
            self.baud_rate,
            rtscts=True,
        )
        self.transport.set_write_buffer_limits(high=131072)

    async def close_serial(self):
        """
        Closes the serial port
        """
        self.transport.close()


class ATErrorException(Exception):
    """
    Exception Class for when the AT command receives an "ERROR"
    """


class ATUnexpectedResponseException(Exception):
    """
    Exception Class for when the AT command receives an unexpected response
    """

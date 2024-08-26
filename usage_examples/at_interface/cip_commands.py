#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the CIP usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    (f"AT+PING={settings.PING_TARGET}\r", r".*\+PING:.*", None),
    (
        f"AT+CIPSTART=0,0,{settings.CIP_TARGET},{settings.CIP_TARGET_PORT}\r",
        r".*\+IP:.*|.*OK.*",
        None,
    ),
    ("AT+CIPSEND=0,11\r", r".*>.*", None),
    ("Hello World", r".*\+IPD:.*|.*OK.*", None),
    ("AT+CIPCLOSE=0\r", r".*\+IP:.*|.*OK.*", None),
]


async def async_main():
    def ip_received(data_str):
        print(f"\r\n{data_str}", end="")

    def ipd_received(data_str):
        print(f"\r\n{data_str}", end="")
    try:
        atsession = serial_service.ATSession(settings.DEVICE, settings.BAUD_RATE)
        await atsession.open_serial()
        atsession.protocol.register_handler("+IP:", ip_received)
        atsession.protocol.register_handler("+IPD:", ipd_received)
        for command in AT_COMMANDS:
            print(command[0], end="")
            response = await atsession.execute_command(*command)
            print(response)
        await atsession.close_serial()
    except Exception as exception:
        print(f"\r\nError running the AT command: {exception}")


asyncio.run(async_main())

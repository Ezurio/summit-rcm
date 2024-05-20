#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the firmware update usage examples
"""

import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+FWSTATUS\r", r".*\+FWSTATUS:.*", None),
    (
        f"AT+FILESUP=4,{settings.FILE_UPLOAD_SIZE},{settings.FILE_UPLOAD_NAME},,1\r",
        r".*>.*|.*OK.*",
        3,
    ),
    ("SEND_FILE",),
    ("AT\r", r".*OK.*", 3),
    ("AT+FWRUN=1,1,\r", r".*OK.*", 3),
    ("AT\r", r".*OK.*", 3),
]


async def async_main():
    try:
        atsession = serial_service.ATSession(settings.DEVICE, settings.BAUD_RATE)
        await atsession.open_serial()
        for command in AT_COMMANDS:
            if "AT+FILESUP" in command[0]:
                fileupcommand = command
                continue
            if command[0] == "SEND_FILE":
                response = await atsession.send_file(
                    settings.FILE_UPLOAD_NAME, fileupcommand
                )
                print(response)
                continue
            print(command[0])
            response = await atsession.execute_command(*command)
            print(response)
        await atsession.close_serial()
    except Exception as exception:
        print(f"\r\nError running the AT command: {str(exception)}")


asyncio.run(async_main())

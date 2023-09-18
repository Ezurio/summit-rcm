"""
File that consists of the fips usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+FIPS\r", r".*\+FIPS:.*", None),
    ("AT+FIPS=1,1\r", r".*OK.*", None),
    ("AT+FIPS\r", r".*\+FIPS:.*", 3),
]


async def async_main():
    try:
        atsession = serial_service.ATSession(settings.DEVICE, settings.BAUD_RATE)
        await atsession.open_serial()
        for command in AT_COMMANDS:
            print(command[0], end="")
            response = await atsession.execute_command(*command)
            print(response)
        await atsession.close_serial()
    except Exception as exception:
        print(f"\r\nError running the AT command: {exception}")


asyncio.run(async_main())

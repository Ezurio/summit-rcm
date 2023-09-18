"""
File that consists of the http usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    (
        f"AT+HTTPCONF={settings.HTTP_HOST},{settings.HTTP_PORT},{settings.HTTP_METHOD},"
        f"{settings.HTTP_ROUTE}\r",
        r".*OK.*",
        None,
    ),
    ("AT+HTTPRSHDR=1\r", r".*OK.*", None),
    ("AT+HTTPADDHDR=foo,bar\r", r".*OK.*", None),
    ("AT+HTTPEXE=11\r", r".*>.*", None),
    ("Hello World", r".*\+HTTPEXE:.*", 0.25),
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

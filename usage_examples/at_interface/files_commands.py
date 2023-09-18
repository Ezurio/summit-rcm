"""
File that consists of the files usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+FILESLIST\r", r".*\+FILESLIST:.*|.*OK.*", None),
    ("AT+CERTGET=ca.crt\r", r".*\+CERTGET:.*", None),
    ("AT+FILESUP=0,11,potato.crt\r", r".*>.*", None),
    ("Hello World\r", r".*OK.*", 0.25),
    ("AT+FILESUP=0,11,potato.pac\r", r".*>.*", None),
    ("Hello World\r", r".*OK.*", 0.25),
    ("AT+FILESLIST\r", r".*\+FILESLIST.*", None),
    ("AT+FILESDEL=potato.crt\r", r".*OK.*", None),
    ("AT+FILESLIST\r", r".*\+FILESLIST.*", None),
    ("AT+FILESEXP=0,3,summit\r", r".*\+FILESEXP.*", None),
    ("AT+FILESEXP=1,3,1000,0\r", r".*\+FILESEXP.*", None),
]


async def async_main():
    try:
        atsession = serial_service.ATSession(settings.DEVICE, settings.BAUD_RATE)
        await atsession.open_serial()
        for command in AT_COMMANDS:
            print(command[0], end="")
            response = await atsession.execute_command(*command)
            if isinstance(response, bytes):
                response = response[:-6]
                print("")
                print(response)
                print("OK")
            else:
                print(response)
        await atsession.close_serial()
    except Exception as exception:
        print(f"\r\nError running the AT command: {exception}")


asyncio.run(async_main())

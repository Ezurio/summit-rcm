"""
File that consists of the datetime usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+DATETIME\r", r".*\+DATETIME:.*", None),
    ("AT+DATETIME=1999999999999999\r", r".*OK.*", None),
    ("AT+DATETIME\r", r".*\+DATETIME:.*", None),
    ("AT+DATETIME=1695659975000000\r", r".*OK.*", None),
    ("AT+NTPGET\r", r".*\+NTPGET:.*|.*OK.*", None),
    ("AT+NTPCONF=0,pool.ntp.org\r", r".*OK.*", None),
    ("AT+NTPGET\r", r".*\+NTPGET:.*|.*OK.*", None),
    ("AT+NTPCONF=1,pool.ntp.org\r", r".*OK.*", None),
    ("AT+TZGET\r", r".*\+TZGET:.*", None),
    ("AT+TZSET=Pacific/Tahiti\r", r".*OK.*", None),
    ("AT+TZGET\r", r".*\+TZGET:.*", None),
    ("AT+TZSET=Etc/UTC\r", r".*OK.*", None),
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

"""
File that consists of the system settings usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE1\r", r".*ATE1.*|.*OK.*", None),
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT\r", r".*OK.*", None),
    ("AT+VER\r", r".*\+VER:.*", None),
    ("AT+NTPGET\r", r".*\+NTPGET:.*|.*OK.*", None),
    ("AT+TZGET\r", r".*\+TZGET:.*", None),
    ("AT+TZGET=1\r", r".*\+TZGET:.*", None),
    ("AT+DATETIME\r", r".*\+DATETIME:.*", None),
    ("AT+AWMMODE\r", r".*\+AWMMODE:.*", None, ("AT\r", r".*OK.*", None)),
    ("AT+AWMSCAN\r", r".*\+AWMSCAN:.*", None, ("AT\r", r".*OK.*", None)),
    ("AT+SISOMODE\r", r".*\+SISOMODE.*", None, ("AT\r", r".*OK.*", None)),
    ("AT+FIPS\r", r".*\+FIPS:.*", None, ("AT\r", r".*OK.*", None)),
    ("AT+LOGDEBUG=0\r", r".*\+LOGDEBUG:.*", None),
    ("AT+LOGDEBUG=1\r", r".*\+LOGDEBUG.*", None),
    ("AT+FILESLIST\r", r".*\+FILESLIST:.*|OK.*", None),
    ("AT+WENABLE\r", r".*\+WENABLE:.*", None),
    ("AT+WHARD\r", r".*\+WHARD:.*", None),
    ("AT+WLIST\r", r".*\+WLIST:.*", 5),
    ("AT+CONNLIST\r", r".*\+CONNLIST:.*", None),
    ("AT+NETIF\r", r".*\+NETIF:.*", None),
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

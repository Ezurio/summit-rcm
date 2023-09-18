"""
File that consists of the network usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+NETIF\r", r".*\+NETIF:.*", None),
    ("AT+NETIF=wlan0\r", r".*\+NETIF:.*", None),
    ("AT+NETIFSTAT=wlan0\r", r".*\+NETIFSTAT:.*", None),
    ("AT+NETIFVIRT=1\r", r".*OK.*", None),
    ("AT+NETIF\r", r".*\+NETIF:.*", 2),
    ("AT+NETIFVIRT=0\r", r".*OK.*", None),
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

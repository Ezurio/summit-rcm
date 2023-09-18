"""
File that consists of the firmware update usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+FWRUN=1,2\r", r".*OK.*", None),
    ("AT+FWSTATUS\r", r".*\+FWSTATUS:.*", None),
    (f"AT+FWSEND={settings.FW_UPDATE_SIZE}\r", r".*>.*", None),
    ("SEND_FILE",),
    ("AT+POWER=3\r", r".*OK.*", None),
    ("AT\r", r".*OK.*", 3),
]


async def async_main():
    try:
        atsession = serial_service.ATSession(settings.DEVICE, settings.BAUD_RATE)
        await atsession.open_serial()
        for command in AT_COMMANDS:
            if command[0] == "SEND_FILE":
                response = await atsession.send_file(settings.FW_UPDATE_FILE)
                print(response)
                continue
            print(command[0], end="")
            response = await atsession.execute_command(*command)
            print(response)
        await atsession.close_serial()
    except Exception as exception:
        print(f"\r\nError running the AT command: {exception}")


asyncio.run(async_main())

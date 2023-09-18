"""
File that consists of the connection usage examples
"""
import asyncio
from typing import Tuple, List
import at_interface_settings as settings
import serial_service


AT_COMMANDS: List[Tuple] = [
    ("ATE0\r", r".*ATE0.*|.*OK.*", None),
    ("AT+CONNLIST\r", r".*\+CONNLIST:.*", None),
    (
        f'AT+CONNMOD=0,{{"connection":{{"autoconnect":1,"id":"{settings.CONNECTION_ID}","interface-'
        f'name":"wlan0","type":"802-11-wireless","uuid":"","zone": "trusted"}},"802-11-wireless":{{'
        f'"mode":"infrastructure","ssid":"{settings.CONNECTION_ID}"}},"802-11-wireless-security":{{'
        f'"key-mgmt":"wpa-psk","psk":"{settings.CONNECTION_PASSWORD}"}}}}\r',
        r".*OK.*",
        None,
    ),
    (f"AT+CONNACT={settings.CONNECTION_ID},1\r", r".*OK.*", None),
    ("AT+CONNLIST\r", r".*\+CONNLIST:.*", 20),
    (f"AT+PING={settings.PING_TARGET}\r", r".*\+PING:.*", None),
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

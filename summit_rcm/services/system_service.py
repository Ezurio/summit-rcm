from syslog import LOG_ERR, syslog
from summit_rcm.utils import Singleton
from dbus_fast import Message, MessageType
from summit_rcm.dbus_manager import DBusManager
import os
from summit_rcm.definition import (
    LOGIND_BUS_NAME,
    LOGIND_MAIN_IFACE,
    LOGIND_MAIN_OBJ,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
)

VALID_POWER_STATES = ["on", "off", "suspend", "reboot"]


class SystemService(metaclass=Singleton):
    def __init__(self) -> None:
        self._state: str = "on"

    @property
    def power_state(self) -> str:
        """
        Retrive the current power state
        """
        return self._state

    async def set_power_state(self, value: str):
        """
        Configure the desired power state for the module. Possible values are:
        - on
        - off
        - suspend
        - reboot
        """
        if value == "on":
            self._state = "on"
        elif value == "off":
            self._state = "off" if await self.__power_off() else "on"
        elif value == "reboot":
            self._state = "reboot" if await self.__reboot() else "on"
        elif value == "suspend":
            self._state = "suspend" if await self.__suspend() else "on"

    async def __power_off(self) -> bool:
        """
        Trigger the module to power off and return a boolean indicating success
        """
        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            return False

        try:
            bus = await DBusManager().get_bus()

            # Call PowerOff() (non-interactive)
            reply = await bus.call(
                Message(
                    destination=LOGIND_BUS_NAME,
                    path=LOGIND_MAIN_OBJ,
                    interface=LOGIND_MAIN_IFACE,
                    member="PowerOff",
                    signature="b",
                    body=[False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            return True
        except Exception as e:
            syslog(LOG_ERR, f"Poweroff cannot be initiated: {str(e)}")
            return False

    async def __reboot(self) -> bool:
        """
        Trigger the module to reboot and return a boolean indicating success
        """
        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            return False

        try:
            bus = await DBusManager().get_bus()

            # Call Reboot() (non-interactive)
            reply = await bus.call(
                Message(
                    destination=LOGIND_BUS_NAME,
                    path=LOGIND_MAIN_OBJ,
                    interface=LOGIND_MAIN_IFACE,
                    member="Reboot",
                    signature="b",
                    body=[False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            return True
        except Exception as e:
            syslog(LOG_ERR, f"Reboot cannot be initiated: {str(e)}")
            return False

    async def __suspend(self) -> bool:
        """
        Trigger the module to suspend and return a boolean indicating success
        """
        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            return False

        try:
            bus = await DBusManager().get_bus()

            # Call Suspend() (non-interactive)
            reply = await bus.call(
                Message(
                    destination=LOGIND_BUS_NAME,
                    path=LOGIND_MAIN_OBJ,
                    interface=LOGIND_MAIN_IFACE,
                    member="Suspend",
                    signature="b",
                    body=[False],
                )
            )

            if reply.message_type == MessageType.ERROR:
                raise Exception(reply.body[0])

            return True
        except Exception as e:
            syslog(LOG_ERR, f"Suspend cannot be initiated: {str(e)}")
            return False

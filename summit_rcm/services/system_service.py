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
from subprocess import call

VALID_POWER_STATES = ["on", "off", "suspend", "reboot"]
FACTORY_RESET_SCRIPT = "/usr/sbin/do_factory_reset.sh"


class SystemService(metaclass=Singleton):
    def __init__(self) -> None:
        self._power_state: str = "on"

    @property
    def power_state(self) -> str:
        """
        Retrive the current power state
        """
        return self._power_state

    async def set_power_state(self, value: str):
        """
        Configure the desired power state for the module. Possible values are:
        - on
        - off
        - suspend
        - reboot
        """
        if value == "on":
            self._power_state = "on"
        elif value == "off":
            self._power_state = "off" if await self.__power_off() else "on"
        elif value == "reboot":
            self._power_state = "reboot" if await self.__reboot() else "on"
        elif value == "suspend":
            self._power_state = "suspend" if await self.__suspend() else "on"

    async def initiate_factory_reset(self) -> int:
        """
        Initiate a factory reset and return an integer returncode indicating success/failure (0 for
        success, non-zero for failure).
        """
        if not os.path.exists(FACTORY_RESET_SCRIPT):
            return -1

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            return -1

        syslog("Factory Reset requested")
        try:
            returncode: int = call([FACTORY_RESET_SCRIPT, "reset"])
        except Exception as e:
            syslog(LOG_ERR, f"FactoryReset error - {str(e)}")
            return -1

        if returncode != 0:
            syslog(LOG_ERR, f"FactoryReset error - returncode: {returncode}")
        return returncode

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

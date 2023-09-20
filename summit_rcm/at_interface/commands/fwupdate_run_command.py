"""
File that consists of the FWUpdateRun Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.firmware_update_service import FirmwareUpdateService


class Modes(IntEnum):
    FWUPDATE_STOP = 0
    FWUPDATE_START = 1


class Image(IntEnum):
    full = 0
    complete = 1
    main = 2


class FWUpdateRunCommand(Command):
    """
    AT Command to start/stop a firmware update
    """

    NAME: str = "Start/Stop Firmware Update"
    SIGNATURE: str = "at+fwrun"
    VALID_NUM_PARAMS: List[int] = [1, 2, 3]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FWUpdateRunCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["mode"] == Modes.FWUPDATE_STOP:
                FirmwareUpdateService().cancel_update()
                return (True, "OK")
            FirmwareUpdateService().start_update(
                params_dict["url"], params_dict["image"]
            )
            return (True, "OK")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error starting/stopping firmware update: {str(exception)}"
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FWUpdateRunCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["mode"] = Modes(int(params_list[0]))
            params_dict["image"] = (
                Image(int(params_list[1])).name if len(params_list) > 1 else ""
            )
        except ValueError:
            return (False, params_dict)
        params_dict["url"] = params_list[2] if len(params_list) > 2 else ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FWRUN=<mode>[,<image>[,<url>]]"

    @staticmethod
    def signature() -> str:
        return FWUpdateRunCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FWUpdateRunCommand.NAME

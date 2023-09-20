"""
File that consists of the LogDebugLevel Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.logs_service import LogsService


class Supp_Levels(IntEnum):
    none = 0
    error = 1
    warning = 2
    info = 3
    debug = 4
    msgdump = 5
    excessive = 6


class Driver_Levels(IntEnum):
    disabled = 0
    enabled = 1


class Types(IntEnum):
    supplicant = 0
    wifi = 1


class LogDebugLevelCommand(Command):
    """
    AT Command to get/set log debug levels of the supplicant or wifi driver
    """

    NAME: str = "Get/Set Log Debug Levels"
    SIGNATURE: str = "at+logdebug"
    VALID_NUM_PARAMS: List[int] = [1, 2]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = LogDebugLevelCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            log_debug_str = ""
            if params_dict["log_level"] != "":
                await LogsService.set_supplicant_debug_level(
                    params_dict["log_level"]
                ) if params_dict[
                    "type"
                ] == Types.supplicant else LogsService.set_wifi_driver_debug_level(
                    params_dict["log_level"]
                )
            else:
                log_debug_str = "+LOGDEBUG: " + (
                    str(Supp_Levels[await LogsService.get_supplicant_debug_level()].value)
                    if params_dict["type"] == Types.supplicant
                    else str(LogsService.get_wifi_driver_debug_level())
                ) + "\r\n"
            return (True, f"{log_debug_str}OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting/setting log debug level: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in LogDebugLevelCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["type"] = Types(int(params_list[0]))
            if len(params_list) > 1:
                if params_dict["type"] == Types.supplicant:
                    params_dict["log_level"] = Supp_Levels(int(params_list[1])).name
                else:
                    params_dict["log_level"] = Driver_Levels(int(params_list[1])).value
            else:
                params_dict["log_level"] = ""
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+LOGDEBUG=<type>[,<log_level>]"

    @staticmethod
    def signature() -> str:
        return LogDebugLevelCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return LogDebugLevelCommand.NAME

"""
File that consists of the SISOMode Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.radio_siso_mode.radio_siso_mode_service import RadioSISOModeService


class Modes(IntEnum):
    SISO_MODE_SYSTEM_DEFAULT = -1
    SISO_MODE_MIMO = 0
    SISO_MODE_ANT0 = 1
    SISO_MODE_ANT1 = 2


class SISOModeCommand(Command):
    """
    AT Command to get/set Radio SISO Mode
    """

    NAME: str = "Get/Set SISO Mode"
    SIGNATURE: str = "at+sisomode"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = SISOModeCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["mode"] == "":
                siso_mode_str = str(RadioSISOModeService().get_current_siso_mode())
                return (True, f"+SISOMODE: {siso_mode_str}\r\nOK")
            RadioSISOModeService().set_siso_mode(params_dict["mode"])
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting/setting Radio SISO Mode: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in SISOModeCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["mode"] = (
                Modes(int(params_list[0])).value if params_list[0] else ""
            )
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+SISOMODE[=<mode>]"

    @staticmethod
    def signature() -> str:
        return SISOModeCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return SISOModeCommand.NAME

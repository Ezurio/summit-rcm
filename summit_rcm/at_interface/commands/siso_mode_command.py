"""
File that consists of the SISOMode Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.radio_siso_mode.radio_siso_mode_service import RadioSISOModeService


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
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {SISOModeCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["mode"] == "":
                siso_mode_str = str(RadioSISOModeService().get_current_siso_mode())
                return (True, f"\r\n+SISOMODE: {siso_mode_str}\r\nOK\r\n")
            RadioSISOModeService().set_siso_mode(params_dict["mode"])
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error getting/setting Radio SISO Mode: {str(exception)}"
            )
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in SISOModeCommand.VALID_NUM_PARAMS
        try:
            params_dict["mode"] = int(params_list[0]) if params_list[0] else ""
            if params_dict["mode"] not in (-1, 0, 1, 2, ""):
                raise ValueError
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+SISOMODE[=<mode>]\r\n"

    @staticmethod
    def signature() -> str:
        return SISOModeCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return SISOModeCommand.NAME

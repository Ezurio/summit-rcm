"""
File that consists of the AWMMode Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.awm.awm_config_service import AWMConfigService


class AWMModeCommand(Command):
    """
    AT Command to get the AWM operating mode
    """

    NAME: str = "Get AWM Operating Mode"
    SIGNATURE: str = "at+awmmode"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = AWMModeCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            awm_lite_str = str(int(AWMConfigService().get_lite_mode_enabled()))
            return (True, f"+AWMMODE: {awm_lite_str}\r\nOK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting AWM operating mode: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in AWMModeCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+AWMMODE"

    @staticmethod
    def signature() -> str:
        return AWMModeCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return AWMModeCommand.NAME

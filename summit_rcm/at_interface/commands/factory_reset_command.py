"""
File that consists of the FactoryReset Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.system_service import SystemService


class FactoryResetCommand(Command):
    """
    AT Command to handle initiating a factory reset
    """

    NAME: str = "Factory Reset"
    SIGNATURE: str = "at+factreset"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FactoryResetCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            return_str = await SystemService().initiate_factory_reset()
            if return_str != 0:
                return (True, "ERROR")
            if params_dict["reboot"]:
                await SystemService().set_power_state("reboot")
            return (True, f"+FACTRESET: {return_str}\r\nOK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error Performing a Factory Reset: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in FactoryResetCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["reboot"] = bool(int(params_list[0])) if params_list[0] != "" else False
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FACTRESET[=<reboot>]"

    @staticmethod
    def signature() -> str:
        return FactoryResetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FactoryResetCommand.NAME

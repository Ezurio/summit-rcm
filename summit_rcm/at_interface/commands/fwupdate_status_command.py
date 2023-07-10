"""
File that consists of the FWUpdateStatus Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.firmware_update_service import FirmwareUpdateService


class FWUpdateStatusCommand(Command):
    """
    AT Command to get status of a firmware update
    """

    NAME: str = "Get firmware update status"
    SIGNATURE: str = "at+fwstatus"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FWUpdateStatusCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {FWUpdateStatusCommand.SIGNATURE}?\r\n",
            )
        try:
            status, info = FirmwareUpdateService().get_update_status()
            return (True, f"\r\n+FWSTATUS: {status.value}\r\nOK\r\n")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error getting firmware update status: {str(exception)}"
            )
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FWUpdateStatusCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+FWSTATUS\r\n"

    @staticmethod
    def signature() -> str:
        return FWUpdateStatusCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FWUpdateStatusCommand.NAME

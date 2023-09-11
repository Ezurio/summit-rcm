"""
File that consists of the CIPClose Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.connection_service import ConnectionService


class CIPCloseCommand(Command):
    """
    AT Command to close an IP connection
    """

    NAME: str = "Close IP connection"
    SIGNATURE: str = "at+cipclose"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPCloseCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "\r\nERROR\r\n")
        try:
            connection_id = int(params_dict["connection_id"])
            if not ConnectionService().connections[
                connection_id
            ].connected or not ConnectionService().close_connection(id=connection_id):
                return (True, "\r\nERROR\r\n")
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error closing the connection: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in CIPCloseCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["connection_id"] = int(params_list[0])
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPCLOSE=<connection id>\r\n"

    @staticmethod
    def signature() -> str:
        return CIPCloseCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CIPCloseCommand.NAME

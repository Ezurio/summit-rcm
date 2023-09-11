"""
File that consists of the HTTPClearConfiguration Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService


class HTTPClearConfiguration(Command):
    """
    AT Command to handle the clearing of HTTP Configurations to default values
    """

    NAME: str = "Clear HTTP Configuration"
    SIGNATURE: str = "at+httpclr"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = HTTPClearConfiguration.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "\r\nERROR\r\n")
        try:
            HTTPService().clear_http_configuration()
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error clearing http configuration: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in HTTPClearConfiguration.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPCLR\r\n"

    @staticmethod
    def signature() -> str:
        return HTTPClearConfiguration.SIGNATURE

    @staticmethod
    def name() -> str:
        return HTTPClearConfiguration.NAME

"""
File that consists of the ClearHTTPConfiguration Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService


class ClearHTTPConfiguration(Command):
    """
    AT Command to handle the clearing of HTTP Configurations to default values
    """
    NAME: str = "Clear HTTP Configuration"
    SIGNATURE: str = "at+httpclr"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ClearHTTPConfiguration.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ClearHTTPConfiguration.SIGNATURE}?\r\n",
            )
        try:
            HTTPService().clear_http_configuration()
            return (True, "\r\nOK\r\n")
        except Exception as e:
            syslog(LOG_ERR, f"error clearing http configuration {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ClearHTTPConfiguration.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPCLR\r\n"

    @staticmethod
    def signature() -> str:
        return ClearHTTPConfiguration.SIGNATURE

    @staticmethod
    def name() -> str:
        return ClearHTTPConfiguration.NAME

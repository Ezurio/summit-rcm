"""
File that consists of the HTTPEnableResponseHeader Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService


class HTTPEnableResponseHeader(Command):
    """
    AT Command to handle the enabling/disabling of HTTP response headers
    """

    NAME: str = "Enable HTTP Response Headers"
    SIGNATURE: str = "at+httprshdr"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = HTTPEnableResponseHeader.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            return_str = HTTPService().enable_response_headers(params_dict["enabled"])
            return (True, f"+HTTPRSHDR: {int(return_str)}\r\nOK")
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error enabling/disabling http response headers: {str(exception)}",
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in HTTPEnableResponseHeader.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["enabled"] = bool(int(params_list[0]))
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+HTTPRSHDR=<enabled>"

    @staticmethod
    def signature() -> str:
        return HTTPEnableResponseHeader.SIGNATURE

    @staticmethod
    def name() -> str:
        return HTTPEnableResponseHeader.NAME

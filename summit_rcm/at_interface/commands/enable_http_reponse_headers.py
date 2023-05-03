"""
File that consists of the EnableHTTPResponseHeader Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.http_service import HTTPService


class EnableHTTPResponseHeader(Command):
    """
    AT Command to handle the enabling/disabling of HTTP response headers
    """
    NAME: str = "Enable HTTP Response Headers"
    SIGNATURE: str = "at+httprshdr"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = EnableHTTPResponseHeader.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {EnableHTTPResponseHeader.SIGNATURE}?\r\n",
            )
        try:
            return_str = HTTPService().enable_response_headers(params_dict["enabled"])
            return (True, f"\r\n+HTTPRSHDR:{return_str}\r\nOK\r\n")
        except Exception as e:
            syslog(LOG_ERR, f"error enabling http response headers {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in EnableHTTPResponseHeader.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        enabled = params_list[0]
        if valid and enabled in ["0", "1"]:
            params_dict["enabled"] = enabled == "1"
        else:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPRSHDR=<enabled>\r\n"

    @staticmethod
    def signature() -> str:
        return EnableHTTPResponseHeader.SIGNATURE

    @staticmethod
    def name() -> str:
        return EnableHTTPResponseHeader.NAME

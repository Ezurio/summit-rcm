"""
File that consists of the HTTPAddHeader Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService


class HTTPAddHeader(Command):
    """
    AT Command to handle adding/updating the configured headers for an HTTP transaction
    """

    NAME: str = "Add HTTP Header"
    SIGNATURE: str = "at+httpaddhdr"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = HTTPAddHeader.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            HTTPService().add_http_header(params_dict["key"], params_dict["value"])
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error adding http header: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in HTTPAddHeader.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["key"] = params_list[0]
        params_dict["value"] = params_list[1]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+HTTPADDHDR=<key>,<value>"

    @staticmethod
    def signature() -> str:
        return HTTPAddHeader.SIGNATURE

    @staticmethod
    def name() -> str:
        return HTTPAddHeader.NAME

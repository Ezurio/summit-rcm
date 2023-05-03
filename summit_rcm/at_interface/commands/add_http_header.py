"""
File that consists of the AddHTTPHeader Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.http_service import HTTPService


class AddHTTPHeader(Command):
    """
    AT Command to handle adding/updating the configured headers for an HTTP transaction
    """
    NAME: str = "Add HTTP Header"
    SIGNATURE: str = "at+httpaddhdr"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = AddHTTPHeader.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {AddHTTPHeader.SIGNATURE}?\r\n",
            )
        try:
            HTTPService().add_http_header(
                params_dict["key"],
                params_dict["value"]
            )
            return (True, "\r\nOK\r\n")
        except Exception as e:
            syslog(LOG_ERR, f"error adding http header {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in AddHTTPHeader.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid:
            params_dict["key"] = params_list[0]
            params_dict["value"] = params_list[1]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPADDHDR=<key>,<value>\r\n"

    @staticmethod
    def signature() -> str:
        return AddHTTPHeader.SIGNATURE

    @staticmethod
    def name() -> str:
        return AddHTTPHeader.NAME

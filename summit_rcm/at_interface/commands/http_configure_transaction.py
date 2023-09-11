"""
File that consists of the HTTPConfigureTransaction Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService

DEFAULT_TIMEOUT = 10


class Types(IntEnum):
    HEAD = 0
    GET = 1
    PUT = 2
    POST = 3
    DELETE = 4
    PATCH = 5


class HTTPConfigureTransaction(Command):
    """
    AT Command to handle the base configuration of an HTTP Transaction
    """

    NAME: str = "Configure HTTP Transaction"
    SIGNATURE: str = "at+httpconf"
    VALID_NUM_PARAMS: List[int] = [4, 5]
    VALID_METHODS: List[str] = ["HEAD", "GET", "PUT", "POST", "DELETE", "PATCH"]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = HTTPConfigureTransaction.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "\r\nERROR\r\n")
        try:
            HTTPService().configure_http_transaction(
                params_dict["host"],
                params_dict["port"],
                params_dict["method"],
                params_dict["route"],
                params_dict["timeout"],
            )
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error configuring http transaction: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in HTTPConfigureTransaction.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["host"] = params_list[0]
        try:
            params_dict["port"] = int(params_list[1])
            params_dict["timeout"] = (
                int(params_list[4]) if len(params_list) > 4 else DEFAULT_TIMEOUT
            )
            params_dict["method"] = Types(int(params_list[2])).name
        except ValueError:
            return (False, params_dict)
        params_dict["route"] = params_list[3]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPCONF=<host>,<port>,<method>,<route>[,timeout]\r\n"

    @staticmethod
    def signature() -> str:
        return HTTPConfigureTransaction.SIGNATURE

    @staticmethod
    def name() -> str:
        return HTTPConfigureTransaction.NAME

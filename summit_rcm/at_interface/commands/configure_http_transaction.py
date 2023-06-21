"""
File that consists of the ConfigureHTTPTransaction Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService

DEFAULT_TIMEOUT = "10"


class ConfigureHTTPTransaction(Command):
    """
    AT Command to handle the base configuration of an HTTP Transaction
    """
    NAME: str = "Configure HTTP Transaction"
    SIGNATURE: str = "at+httpconf"
    VALID_NUM_PARAMS: List[int] = [4, 5]
    VALID_METHODS: List[str] = ["HEAD", "GET", "PUT", "POST", "DELETE", "PATCH"]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConfigureHTTPTransaction.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ConfigureHTTPTransaction.SIGNATURE}?\r\n",
            )
        try:
            HTTPService().configure_http_transaction(
                params_dict["host"],
                params_dict["port"],
                params_dict["method"],
                params_dict["route"],
                params_dict["timeout"],
            )
            return (True, "\r\nOK\r\n")
        except Exception as e:
            syslog(LOG_ERR, f"error configuring http transaction {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ConfigureHTTPTransaction.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid:
            params_dict["host"] = params_list[0]
            try:
                params_dict["port"] = int(params_list[1])
                params_dict["timeout"] = (
                    int(params_list[4]) if len(params_list) > 4 else DEFAULT_TIMEOUT
                )
            except ValueError:
                valid = False
            if params_list[2].upper() in ConfigureHTTPTransaction.VALID_METHODS:
                params_dict["method"] = params_list[2].upper()
            else:
                valid = False
            params_dict["route"] = params_list[3]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPCONF=<host>,<port>,<method>,<route>[,timeout]\r\n"

    @staticmethod
    def signature() -> str:
        return ConfigureHTTPTransaction.SIGNATURE

    @staticmethod
    def name() -> str:
        return ConfigureHTTPTransaction.NAME

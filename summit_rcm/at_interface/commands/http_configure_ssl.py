"""
File that consists of the ConfigureHTTPSSL Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService
from summit_rcm.services.files_service import SUMMIT_RCM_CLIENT_SSL_DIR
from summit_rcm.definition import SSLModes


class Hostname(IntEnum):
    CHECK_HOSTNAME_FALSE = 0
    CHECK_HOSTNAME_TRUE = 1


class HTTPConfigureSSL(Command):
    """
    AT Command to handle configuring SSL for the HTTP transaction
    """

    NAME: str = "Configure HTTP SSL"
    SIGNATURE: str = "at+httpssl"
    VALID_NUM_PARAMS: List[int] = [5]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = HTTPConfigureSSL.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            HTTPService().configure_http_ssl(
                params_dict["auth_mode"].value,
                params_dict["check_hostname"],
                SUMMIT_RCM_CLIENT_SSL_DIR + params_dict["key"],
                SUMMIT_RCM_CLIENT_SSL_DIR + params_dict["cert"],
                SUMMIT_RCM_CLIENT_SSL_DIR + params_dict["ca"],
            )
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error configuring https transaction: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        length = len(params_list)
        valid &= length in HTTPConfigureSSL.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["auth_mode"] = SSLModes(int(params_list[0]))
            if params_dict["auth_mode"] == SSLModes.DISABLED:
                raise ValueError
            params_dict["check_hostname"] = (
                bool(Hostname(int(params_list[1])).value) if params_list[1] else ""
            )
        except ValueError:
            return (False, params_dict)
        params_dict["key"] = params_list[2]
        params_dict["cert"] = params_list[3]
        params_dict["ca"] = params_list[4]
        mode = params_dict["auth_mode"]
        hostname = params_dict["check_hostname"]
        key = params_dict["key"]
        cert = params_dict["cert"]
        ca = params_dict["ca"]
        if mode == SSLModes.SERVER_VERIFY_CLIENT and (key == "" or cert == ""):
            return (False, params_dict)
        if mode == SSLModes.CLIENT_VERIFY_SERVER and (ca == "" or hostname == ""):
            return (False, params_dict)
        if mode == SSLModes.MUTUAL_AUTH and (
            key == "" or cert == "" or ca == "" or hostname == ""
        ):
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+HTTPSSL=<auth_mode>[,<check_hostname>][,<key>,<cert>][,<ca>]"

    @staticmethod
    def signature() -> str:
        return HTTPConfigureSSL.SIGNATURE

    @staticmethod
    def name() -> str:
        return HTTPConfigureSSL.NAME

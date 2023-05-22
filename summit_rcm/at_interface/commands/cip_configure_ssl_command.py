"""
File that consists of the CIPSSL Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.connection_service import ConnectionService
from summit_rcm.services.files_service import SUMMIT_RCM_CLIENT_SSL_DIR
from summit_rcm.definition import SSLModes


class Hostname(IntEnum):
    CHECK_HOSTNAME_FALSE = 0
    CHECK_HOSTNAME_TRUE = 1


class CIPConfigureSSL(Command):
    """
    AT Command to handle configuring SSL for the CIP connection
    """

    NAME: str = "Configure CIP SSL"
    SIGNATURE: str = "at+cipssl"
    VALID_NUM_PARAMS: List[int] = [6]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPConfigureSSL.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            ConnectionService().configure_cip_ssl(
                params_dict["connection_id"],
                params_dict["auth_mode"].value,
                params_dict["check_hostname"],
                SUMMIT_RCM_CLIENT_SSL_DIR + params_dict["key"],
                SUMMIT_RCM_CLIENT_SSL_DIR + params_dict["cert"],
                SUMMIT_RCM_CLIENT_SSL_DIR + params_dict["ca"],
            )
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error configuring CIP SSL connection: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        length = len(params_list)
        valid &= length in CIPConfigureSSL.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["connection_id"] = int(params_list[0])
            params_dict["auth_mode"] = SSLModes(int(params_list[1]))
            if params_dict["auth_mode"] == SSLModes.DISABLED:
                raise ValueError
            params_dict["check_hostname"] = (
                bool(Hostname(int(params_list[2])).value) if params_list[2] else ""
            )
        except ValueError:
            return (False, params_dict)
        params_dict["key"] = params_list[3]
        params_dict["cert"] = params_list[4]
        params_dict["ca"] = params_list[5]
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
        return "AT+CIPSSL=<connection_id>,<auth_mode>[,<check_hostname>][,<key>,<cert>][,<ca>]"

    @staticmethod
    def signature() -> str:
        return CIPConfigureSSL.SIGNATURE

    @staticmethod
    def name() -> str:
        return CIPConfigureSSL.NAME

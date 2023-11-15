"""
File that consists of the CertificatesGet Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from json import dumps
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.certificates_service import CertificatesService


class CertificatesGetCommand(Command):
    """
    AT Command to get information on a certificate or list all certificates
    """

    NAME: str = "Certificates Get"
    SIGNATURE: str = "at+certget"
    VALID_NUM_PARAMS: List[int] = [2]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CertificatesGetCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            certificates_dict, return_msg = CertificatesService.get_cert_info(
                params_dict["name"], params_dict["password"]
            )
            if return_msg == "":
                certificates_str = dumps(certificates_dict, separators=(",", ":"))
                return (True, f"+CERTGET: {certificates_str}\r\nOK")
            raise Exception(return_msg)
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting certificate information: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in CertificatesGetCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        params_dict["name"] = params_list[0]
        params_dict["password"] = params_list[1]
        if params_dict["name"] == "":
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+CERTGET=<name>[,<password>]"

    @staticmethod
    def signature() -> str:
        return CertificatesGetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CertificatesGetCommand.NAME

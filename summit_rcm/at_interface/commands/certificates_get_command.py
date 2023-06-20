"""
File that consists of the CertificatesGet Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from json import dumps
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.certificates_service import CertificatesService
from summit_rcm.rest_api.legacy.files import FilesManage


class CertificatesGetCommand(Command):
    """
    AT Command to get information on a certificate or list all certificates
    """

    NAME: str = "Certificates Get"
    SIGNATURE: str = "at+certget"
    VALID_NUM_PARAMS: List[int] = [1, 2]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CertificatesGetCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {CertificatesGetCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["name"]:
                certificates_dict, return_msg = CertificatesService.get_cert_info(
                    params_dict["name"], params_dict["password"]
                )
                if return_msg == "":
                    certificates_str = dumps(certificates_dict, separators=(',', ':'))
                    return (True, f"\r\n+CERTGET: {certificates_str}\r\nOK\r\n")
                raise Exception(return_msg)
            certificates_str = ""
            files = FilesManage.get_cert_or_pac_files("cert")
            for file in files:
                certificates_str += f"+CERTGET: {file}\r\n"
            return (True, f"\r\n{certificates_str}OK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting certificate information: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in CertificatesGetCommand.VALID_NUM_PARAMS
        params_dict["name"] = params_list[0]
        params_dict["password"] = None if len(params_list) < 2 else params_list[1]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CERTGET[=<name>[,<password>]]\r\n"

    @staticmethod
    def signature() -> str:
        return CertificatesGetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CertificatesGetCommand.NAME

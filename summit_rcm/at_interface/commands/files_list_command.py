"""
File that consists of the FilesList Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.files_service import FilesService


class Types(IntEnum):
    FILE_TYPE_CERT_AND_PAC = 0
    FILE_TYPE_CERT = 1
    FILE_TYPE_PAC = 2


class FilesListCommand(Command):
    """
    AT Command to list Cert and/or Pac Files
    """

    NAME: str = "List Cert and/or Pac Files"
    SIGNATURE: str = "at+fileslist"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FilesListCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "\r\nERROR\r\n")
        try:
            files_str = ""
            if params_dict["type"] == Types.FILE_TYPE_CERT_AND_PAC:
                files_list = FilesService().get_cert_and_pac_files()
            elif params_dict["type"] == Types.FILE_TYPE_CERT:
                files_list = FilesService().get_cert_files()
            else:
                files_list = FilesService().get_pac_files()
            for file in files_list:
                files_str += f"+FILESLIST: {file}\r\n"
            return (True, f"\r\n{files_str}OK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting cert and/or pac files: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FilesListCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["type"] = (
                Types(int(params_list[0])) if params_list[0] else Types(0)
            )
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+FILESLIST[=<type>]\r\n"

    @staticmethod
    def signature() -> str:
        return FilesListCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FilesListCommand.NAME

"""
File that consists of the FilesUpload Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.files_service import FilesService
from summit_rcm.at_interface.services.at_files_service import ATFilesService
import summit_rcm.at_interface.fsm as fsm


class Types(IntEnum):
    FILE_TYPE_CERT = 0
    FILE_TYPE_CONNECTION = 1
    FILE_TYPE_CONFIG = 2


class Modes(IntEnum):
    OVERWRITE = 0
    APPEND = 1


MODES_DICT = {Modes.OVERWRITE: "wb", Modes.APPEND: "ab"}


class FilesUploadCommand(Command):
    """
    AT Command to upload a cert, connection, or config file
    """

    NAME: str = "Upload Files"
    SIGNATURE: str = "at+filesup"
    VALID_NUM_PARAMS: List[int] = [5]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FilesUploadCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if not ATFilesService().transfer_in_process():
                fsm.ATInterfaceFSM().at_output("> ", print_trailing_line_break=False)
            done, body, length = await ATFilesService().write_upload_body(
                params_dict["length"]
            )
            if not done:
                return (False, "")
            if length == -1:
                syslog(LOG_ERR, "Escaping Data Mode")
                fsm.ATInterfaceFSM().at_output("\r\n", False, False)
                return (True, "")
            file_type = params_dict["type"]
            if file_type == Types.FILE_TYPE_CERT:
                await FilesService.handle_cert_file_upload_bytes(
                    body, params_dict["name"], MODES_DICT[params_dict["mode"]]
                )
            elif file_type == Types.FILE_TYPE_CONNECTION:
                await FilesService.handle_connection_import_file_upload_bytes(
                    body, MODES_DICT[params_dict["mode"]]
                )
                success, message = await FilesService.import_connections(
                    params_dict["password"], False
                )
                if not success:
                    raise Exception(message)
            else:
                await FilesService.handle_config_import_file_upload_bytes(
                    body, MODES_DICT[params_dict["mode"]]
                )
                success, message = await FilesService.import_system_config(
                    params_dict["password"]
                )
                if not success:
                    raise Exception(message)
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error uploading file: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FilesUploadCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["type"] = Types(int(params_list[0]))
            params_dict["length"] = int(params_list[1])
            params_dict["name"] = params_list[2]
            params_dict["password"] = params_list[3]
            params_dict["mode"] = (
                Modes(int(params_list[4])) if params_list[4] else Modes.OVERWRITE
            )
        except ValueError:
            return (False, params_dict)
        type = params_dict["type"]
        password = params_dict["password"]
        if type == Types.FILE_TYPE_CERT and params_dict["name"] == "":
            return (False, params_dict)
        if type == Types.FILE_TYPE_CONNECTION and password == "":
            return (False, params_dict)
        if type == Types.FILE_TYPE_CONFIG and password == "":
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FILESUP=<type>,<length>[,<name>][,<password>][,<mode>]"

    @staticmethod
    def signature() -> str:
        return FilesUploadCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FilesUploadCommand.NAME

"""
File that consists of the FilesExport Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
import os
import summit_rcm.at_interface.fsm as fsm
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.files_service import (
    FilesService,
    CONNECTION_TMP_ARCHIVE_FILE,
    CONFIG_TMP_ARCHIVE_FILE,
    LOG_TMP_ARCHIVE_FILE,
    DEBUG_TMP_ARCHIVE_FILE,
)


class Types(IntEnum):
    FILE_TYPE_CONFIG = 0
    FILE_TYPE_LOGS = 1
    FILE_TYPE_DEBUG = 2
    FILE_TYPE_CONNECTION = 3


PATHS = {
    Types.FILE_TYPE_CONFIG: CONFIG_TMP_ARCHIVE_FILE,
    Types.FILE_TYPE_LOGS: LOG_TMP_ARCHIVE_FILE,
    Types.FILE_TYPE_DEBUG: DEBUG_TMP_ARCHIVE_FILE,
    Types.FILE_TYPE_CONNECTION: CONNECTION_TMP_ARCHIVE_FILE,
}

MAX_FILE_CHUNK_SIZE = 128 * 1024


class FilesExportCommand(Command):
    """
    AT Command to export a zip archive for NetworkManager
    """

    NAME: str = "Export Zip Archive"
    SIGNATURE: str = "at+filesexp"
    VALID_NUM_PARAMS: List[int] = [2, 3, 4]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FilesExportCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["mode"]:
                file = await FilesService().handle_file_download(params_dict["path"])
                await file.seek(params_dict["offset"])
                file_chunk = await file.read(params_dict["chunk size"])
                file_chunk_size = len(file_chunk)
                fsm.ATInterfaceFSM().at_output(
                    f"+FILESEXP: {file_chunk_size},", print_trailing_line_break=False
                )
                fsm.ATInterfaceFSM().at_output(file_chunk, False, False)
                return (
                    True,
                    "OK",
                )
            filetype = params_dict["type"]
            if filetype == Types.FILE_TYPE_CONFIG:
                if not FilesService.is_encrypted_storage_toolkit_enabled():
                    raise Exception(
                        "Config export not supported on non-encrypted file system images"
                    )
                success, message, path = FilesService().export_system_config(
                    params_dict["password"]
                )
            elif filetype == Types.FILE_TYPE_DEBUG:
                success, message, path = FilesService().export_debug()
            elif filetype == Types.FILE_TYPE_LOGS:
                success, message, path = FilesService().export_logs(
                    params_dict["password"]
                )
            else:
                success, message, path = FilesService().export_connections(
                    params_dict["password"]
                )
            if success:
                return (
                    True,
                    f"+FILESEXP: {str(os.path.getsize(path))}\r\nOK",
                )
            raise Exception(message)
        except Exception as exception:
            syslog(LOG_ERR, f"Error exporting zip archive: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        length = len(params_list)
        valid &= length in FilesExportCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["mode"] = bool(int(params_list[0]))
            if params_dict["mode"] and length != 4:
                raise ValueError
            params_dict["chunk size"] = (
                int(params_list[2]) if (params_dict["mode"] and length > 2) else 0
            )
            if params_dict["chunk size"] > MAX_FILE_CHUNK_SIZE:
                raise ValueError
            params_dict["offset"] = (
                int(params_list[3]) if (params_dict["mode"] and length > 3) else 0
            )
            params_dict["type"] = Types(int(params_list[1]))
        except ValueError:
            return (False, params_dict)
        params_dict["path"] = PATHS[params_dict["type"]]
        params_dict["password"] = (
            ""
            if (
                params_dict["type"] == Types.FILE_TYPE_DEBUG
                or length < 3
                or params_dict["mode"]
            )
            else params_list[2]
        )
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FILESEXP=<mode>,<type>[,<password>][,<chunk size>,<offset>]"

    @staticmethod
    def signature() -> str:
        return FilesExportCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FilesExportCommand.NAME

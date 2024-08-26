#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the FilesDelete Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.files_service import FilesService


class FilesDeleteCommand(Command):
    """
    AT Command to delete a certificate file
    """

    NAME: str = "Delete certificate file"
    SIGNATURE: str = "at+filesdel"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FilesDeleteCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            FilesService().delete_cert_file(params_dict["name"])
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error deleting certificate file: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FilesDeleteCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["name"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FILESDEL=<name>"

    @staticmethod
    def signature() -> str:
        return FilesDeleteCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FilesDeleteCommand.NAME

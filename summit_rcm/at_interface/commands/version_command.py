#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the Version Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.definition import SUMMIT_RCM_VERSION


class VersionCommand(Command):
    """
    AT Command to get the Summit-RCM version
    """

    NAME: str = "Version"
    SIGNATURE: str = "at+ver"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = VersionCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        return (True, f"+VER: {SUMMIT_RCM_VERSION}\r\nOK")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in VersionCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+VER"

    @staticmethod
    def signature() -> str:
        return VersionCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return VersionCommand.NAME

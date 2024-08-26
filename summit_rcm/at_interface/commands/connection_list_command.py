#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the ConnectionList Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class ConnectionListCommand(Command):
    """
    AT Command to list network connections
    """

    NAME: str = "List Connections"
    SIGNATURE: str = "at+connlist"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionListCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            connections_str = ""
            connections_list = await NetworkService().get_all_connection_profiles()
            for connection in connections_list:
                connections_str += f"+CONNLIST: {connection['uuid']}:{connection['id']},{connection['activated']}\r\n"
            return (True, f"{connections_str}OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error listing network connection: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ConnectionListCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+CONNLIST"

    @staticmethod
    def signature() -> str:
        return ConnectionListCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ConnectionListCommand.NAME

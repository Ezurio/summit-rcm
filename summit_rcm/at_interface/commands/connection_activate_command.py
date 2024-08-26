#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the ConnectionActivate Command Functionality
"""
from typing import List, Tuple
from syslog import syslog, LOG_ERR
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService
from summit_rcm.services.network_service import ConnectionProfileNotFoundError


class ConnectionActivateCommand(Command):
    """
    AT Command to activate or deactivate a connection profile
    """

    NAME: str = "Activate/Deactivate Connection"
    SIGNATURE: str = "at+connact"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionActivateCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            try:
                uuid = await NetworkService().get_connection_profile_uuid_from_id(
                    params_dict["profile"]
                )
            except ConnectionProfileNotFoundError:
                uuid = params_dict["profile"]
            if params_dict["activate"]:
                await NetworkService().activate_connection_profile(uuid=uuid)
            else:
                await NetworkService().deactivate_connection_profile(uuid=uuid)
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error Activating Connection: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in ConnectionActivateCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["profile"] = params_list[0]
        try:
            params_dict["activate"] = int(params_list[1])
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+CONNACT=<uuid>|<id>,<activate>"

    @staticmethod
    def signature() -> str:
        return ConnectionActivateCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ConnectionActivateCommand.NAME

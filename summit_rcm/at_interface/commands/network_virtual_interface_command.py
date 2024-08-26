#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the NetworkVirtualInterface Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class Modes(IntEnum):
    REMOVE = 0
    ADD = 1


class NetworkVirtualInterfaceCommand(Command):
    """
    AT Command to add or remove a virtual interface
    """

    NAME: str = "Virtual Interface"
    SIGNATURE: str = "at+netifvirt"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = NetworkVirtualInterfaceCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["add"] == Modes.ADD:
                await NetworkService().add_virtual_interface()
            else:
                await NetworkService().remove_virtual_interface()
            return (True, "OK")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error adding/removing virtual interface: {str(exception)}"
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in NetworkVirtualInterfaceCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["add"] = Modes(int(params_list[0]))
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+NETIFVIRT=<add>"

    @staticmethod
    def signature() -> str:
        return NetworkVirtualInterfaceCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return NetworkVirtualInterfaceCommand.NAME

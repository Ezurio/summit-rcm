#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the NetworkInterfaces Command Functionality
"""
from json import dumps
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class NetworkInterfacesCommand(Command):
    """
    AT Command to list network interfaces, or query the status of a specific interface
    """

    NAME: str = "Network Interfaces"
    SIGNATURE: str = "at+netif"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = NetworkInterfacesCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            interfaces_string = ""
            ifname = params_dict["interface name"]
            interfaces_list = await NetworkService.get_all_interfaces()
            if not ifname:
                for interface in interfaces_list:
                    interfaces_string += f"{interface},"
                interfaces_string = interfaces_string[:-1]
            elif ifname not in interfaces_list:
                return (True, "ERROR")
            else:
                interfaces_dict = await NetworkService.get_interface_status(
                    ifname, is_legacy=False
                )
                interfaces_string = dumps(interfaces_dict, separators=(",", ":"))
            return (True, f"+NETIF: {interfaces_string}\r\nOK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting network interfaces: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in NetworkInterfacesCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        params_dict["interface name"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+NETIF[=<interface name>]"

    @staticmethod
    def signature() -> str:
        return NetworkInterfacesCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return NetworkInterfacesCommand.NAME

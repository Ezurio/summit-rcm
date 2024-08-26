#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the NetworkInterfaceStatistics Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class NetworkInterfaceStatisticsCommand(Command):
    """
    AT Command to retrieve statistics on a specific network interface
    """

    NAME: str = "Network Interface Statistics"
    SIGNATURE: str = "at+netifstat"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = NetworkInterfaceStatisticsCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            (success, statistics_dict) = await NetworkService.get_interface_statistics(
                params_dict["interface name"], is_legacy=False
            )
            statistics_str = f"{statistics_dict['rxBytes']},"
            statistics_str += f"{statistics_dict['rxPackets']},"
            statistics_str += f"{statistics_dict['rxErrors']},"
            statistics_str += f"{statistics_dict['rxDropped']},"
            statistics_str += f"{statistics_dict['multicast']},"
            statistics_str += f"{statistics_dict['txBytes']},"
            statistics_str += f"{statistics_dict['txPackets']},"
            statistics_str += f"{statistics_dict['txErrors']},"
            statistics_str += f"{statistics_dict['txDropped']}"
            return (True, f"+NETIFSTAT: {statistics_str}\r\nOK")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error getting network interface statistics: {str(exception)}"
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in NetworkInterfaceStatisticsCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["interface name"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+NETIFSTAT=<interface name>"

    @staticmethod
    def signature() -> str:
        return NetworkInterfaceStatisticsCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return NetworkInterfaceStatisticsCommand.NAME
